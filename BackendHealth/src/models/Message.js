const mongoose = require('mongoose');

const messageSchema = new mongoose.Schema({
  conversationId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Conversation',
    required: true,
    index: true
  },
  sessionId: {
    type: String,
    required: true,
    index: true
  },
  messageId: {
    type: String,
    required: true,
    unique: true
  },
  role: {
    type: String,
    enum: ['user', 'assistant', 'system'],
    required: true
  },
  content: {
    text: String,
    images: [{
      url: String,
      cloudStorageKey: String,
      metadata: {
        size: Number,
        mimeType: String,
        dimensions: {
          width: Number,
          height: Number
        }
      }
    }],
    attachments: [{
      fileName: String,
      url: String,
      cloudStorageKey: String,
      size: Number,
      mimeType: String
    }]
  },
  metadata: {
    timestamp: {
      type: Date,
      default: Date.now
    },
    processingTime: Number,
    tokenCount: Number,
    confidence: Number
  }
}, {
  timestamps: true
});

messageSchema.index({ conversationId: 1, createdAt: 1 });
messageSchema.index({ sessionId: 1, createdAt: -1 });

module.exports = mongoose.model('Message', messageSchema);