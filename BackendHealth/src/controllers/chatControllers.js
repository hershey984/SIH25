const chatService = require('../services/chatService');
const cacheService = require('../services/cacheService');

class ChatController {
  async createConversation(req, res) {
    try {
      const { userId, type, metadata } = req.body;
      
      const conversation = await chatService.createConversation(userId, type, metadata);
      
      res.status(201).json({
        success: true,
        data: {
          sessionId: conversation.sessionId,
          conversationId: conversation._id,
          type: conversation.type,
          createdAt: conversation.createdAt
        }
      });
    } catch (error) {
      res.status(500).json({
        success: false,
        message: error.message
      });
    }
  }

  async sendMessage(req, res) {
    try {
      const { sessionId } = req.params;
      const { message, role = 'user' } = req.body;
      const files = req.files;

      const savedMessage = await chatService.addMessage(sessionId, role, message, files);

      // Track user activity
      await cacheService.trackUserActivity(savedMessage.conversationId, {
        type: 'message_sent',
        sessionId,
        timestamp: new Date()
      });

      res.status(201).json({
        success: true,
        data: savedMessage
      });
    } catch (error) {
      res.status(500).json({
        success: false,
        message: error.message
      });
    }
  }

  async getMessages(req, res) {
    try {
      const { sessionId } = req.params;
      const { page = 1, limit = 50 } = req.query;

      const messages = await chatService.getMessages(sessionId, parseInt(page), parseInt(limit));

      res.json({
        success: true,
        data: messages,
        pagination: {
          page: parseInt(page),
          limit: parseInt(limit),
          total: messages.length
        }
      });
    } catch (error) {
      res.status(500).json({
        success: false,
        message: error.message
      });
    }
  }

  async getConversations(req, res) {
    try {
      const { userId } = req.params;
      const { page = 1, limit = 20 } = req.query;

      const conversations = await chatService.getUserConversations(userId, parseInt(page), parseInt(limit));

      res.json({
        success: true,
        data: conversations
      });
    } catch (error) {
      res.status(500).json({
        success: false,
        message: error.message
      });
    }
  }

  async deleteConversation(req, res) {
    try {
      const { sessionId } = req.params;
      const { userId } = req.body;

      await chatService.deleteConversation(sessionId, userId);

      res.json({
        success: true,
        message: 'Conversation deleted successfully'
      });
    } catch (error) {
      res.status(500).json({
        success: false,
        message: error.message
      });
    }
  }

  async backupConversation(req, res) {
    try {
      const { sessionId } = req.params;

      const backupKey = await chatService.backupConversation(sessionId);

      res.json({
        success: true,
        data: { backupKey },
        message: 'Conversation backed up successfully'
      });
    } catch (error) {
      res.status(500).json({
        success: false,
        message: error.message
      });
    }
  }
}

module.exports = new ChatController();