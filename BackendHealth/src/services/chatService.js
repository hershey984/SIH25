const { v4: uuidv4 } = require('uuid');
const Conversation = require('../models/Conversation');
const Message = require('../models/Message');
const cacheService = require('./cacheService');
const storageService = require('./storageService');

class ChatService {
  async createConversation(userId, type = 'general', metadata = {}) {
    const sessionId = uuidv4();
    
    // Create conversation in database
    const conversation = new Conversation({
      sessionId,
      userId,
      type,
      metadata,
      lastActivity: new Date()
    });

    await conversation.save();

    // Cache the conversation
    await cacheService.cacheConversation(sessionId, {
      id: conversation._id,
      sessionId,
      userId,
      type,
      createdAt: conversation.createdAt
    });

    return conversation;
  }

  async getConversation(sessionId) {
    // Try cache first
    let conversation = await cacheService.getCachedConversation(sessionId);
    
    if (!conversation) {
      // Fallback to database
      const dbConversation = await Conversation.findOne({ sessionId, isActive: true });
      if (dbConversation) {
        conversation = {
          id: dbConversation._id,
          sessionId: dbConversation.sessionId,
          userId: dbConversation.userId,
          type: dbConversation.type,
          createdAt: dbConversation.createdAt
        };
        // Cache for next time
        await cacheService.cacheConversation(sessionId, conversation);
      }
    }
    
    return conversation;
  }

  async addMessage(sessionId, role, content, files = []) {
    const conversation = await this.getConversation(sessionId);
    if (!conversation) {
      throw new Error('Conversation not found');
    }

    const messageId = uuidv4();
    const messageData = {
      conversationId: conversation.id,
      sessionId,
      messageId,
      role,
      content: { text: content, images: [], attachments: [] },
      metadata: {
        timestamp: new Date(),
        tokenCount: content ? content.length : 0
      }
    };

    // Handle file uploads
    if (files && files.length > 0) {
      for (const file of files) {
        const uploadResult = await storageService.uploadFile(file, `conversations/${sessionId}`);
        
        if (file.mimetype.startsWith('image/')) {
          messageData.content.images.push({
            url: uploadResult.url,
            cloudStorageKey: uploadResult.key,
            metadata: {
              size: uploadResult.size,
              mimeType: uploadResult.mimeType
            }
          });
        } else {
          messageData.content.attachments.push({
            fileName: file.originalname,
            url: uploadResult.url,
            cloudStorageKey: uploadResult.key,
            size: uploadResult.size,
            mimeType: uploadResult.mimeType
          });
        }
      }
    }

    // Save to database
    const message = new Message(messageData);
    await message.save();

    // Cache the message for real-time access
    await cacheService.addMessage(sessionId, messageData);

    // Update conversation activity
    await Conversation.findByIdAndUpdate(conversation.id, {
      lastActivity: new Date(),
      $inc: { messageCount: 1 }
    });

    return message;
  }

  async getMessages(sessionId, page = 1, limit = 50) {
    // For recent messages, try cache first
    if (page === 1 && limit <= 10) {
      const cachedMessages = await cacheService.getRecentMessages(sessionId, limit);
      if (cachedMessages.length > 0) {
        return cachedMessages;
      }
    }

    // Fallback to database with pagination
    const conversation = await this.getConversation(sessionId);
    if (!conversation) {
      throw new Error('Conversation not found');
    }

    const skip = (page - 1) * limit;
    const messages = await Message.find({ conversationId: conversation.id })
      .sort({ createdAt: -1 })
      .skip(skip)
      .limit(limit)
      .lean();

    return messages.reverse(); // Return in chronological order
  }

  async getUserConversations(userId, page = 1, limit = 20) {
    const skip = (page - 1) * limit;
    
    const conversations = await Conversation.find({ 
      userId, 
      isActive: true 
    })
    .sort({ lastActivity: -1 })
    .skip(skip)
    .limit(limit)
    .select('sessionId title type lastActivity messageCount createdAt')
    .lean();

    return conversations;
  }

  async deleteConversation(sessionId, userId) {
    const conversation = await Conversation.findOne({ sessionId, userId });
    if (!conversation) {
      throw new Error('Conversation not found');
    }

    // Mark as inactive instead of deleting (for data retention)
    await Conversation.findByIdAndUpdate(conversation._id, { isActive: false });

    // Clean up cache
    await cacheService.deleteSession(sessionId);

    return true;
  }

  async backupConversation(sessionId) {
    const conversation = await this.getConversation(sessionId);
    if (!conversation) {
      throw new Error('Conversation not found');
    }

    const messages = await this.getMessages(sessionId, 1, 1000); // Get all messages
    
    const backupData = {
      conversation,
      messages,
      backedUpAt: new Date()
    };

    const backupKey = await storageService.backupConversation(conversation.id, backupData);
    return backupKey;
  }
}

module.exports = new ChatService();