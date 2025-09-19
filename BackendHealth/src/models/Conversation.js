const mongoose = require('mongoose');

const conversationSchema = new mongoose.Schema({
  sessionId: {
    type: String,
    required: true,
    unique: true,
    index: true
  },
  userId: {
    type: String,
    required: true,
    index: true
  },
  title: {
    type: String,
    default: 'New Conversation'
  },
  type: {
    type: String,
    enum: ['general', 'plant_doctor', 'knowledge'],
    default: 'general'
  },
  metadata: {
    userAgent: String,
    ipAddress: String,
    language: String,
    platform: String
  },
  isActive: {
    type: Boolean,
    default: true
  },
  lastActivity: {
    type: Date,
    default: Date.now
  },
  messageCount: {
    type: Number,
    default: 0
  }
}, {
  timestamps: true
});

conversationSchema.index({ userId: 1, createdAt: -1 });
conversationSchema.index({ sessionId: 1, isActive: 1 });

module.exports = mongoose.model('Conversation', conversationSchema);