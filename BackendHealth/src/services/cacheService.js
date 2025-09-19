const redis = require('../config/redis');

class CacheService {
  // Session management
  async setSession(sessionId, data, expire = 3600) {
    const key = `session:${sessionId}`;
    await redis.setex(key, expire, JSON.stringify(data));
  }

  async getSession(sessionId) {
    const key = `session:${sessionId}`;
    const data = await redis.get(key);
    return data ? JSON.parse(data) : null;
  }

  async deleteSession(sessionId) {
    const key = `session:${sessionId}`;
    await redis.del(key);
  }

  // Conversation caching
  async cacheConversation(sessionId, conversation) {
    const key = `conversation:${sessionId}`;
    await redis.setex(key, 3600, JSON.stringify(conversation));
  }

  async getCachedConversation(sessionId) {
    const key = `conversation:${sessionId}`;
    const data = await redis.get(key);
    return data ? JSON.parse(data) : null;
  }

  // Message caching for real-time chat
  async addMessage(sessionId, message) {
    const key = `messages:${sessionId}`;
    await redis.lpush(key, JSON.stringify(message));
    await redis.expire(key, 3600);
    
    // Keep only last 50 messages in cache
    await redis.ltrim(key, 0, 49);
  }

  async getRecentMessages(sessionId, count = 10) {
    const key = `messages:${sessionId}`;
    const messages = await redis.lrange(key, 0, count - 1);
    return messages.map(msg => JSON.parse(msg));
  }

  // Knowledge feed caching
  async cacheKnowledgeFeed(feedId, data, expire = 1800) {
    const key = `knowledge:${feedId}`;
    await redis.setex(key, expire, JSON.stringify(data));
  }

  async getCachedKnowledgeFeed(feedId) {
    const key = `knowledge:${feedId}`;
    const data = await redis.get(key);
    return data ? JSON.parse(data) : null;
  }

  // Plant doctor report caching
  async cachePlantDoctorReport(reportId, data, expire = 7200) {
    const key = `doctor:${reportId}`;
    await redis.setex(key, expire, JSON.stringify(data));
  }

  async getCachedPlantDoctorReport(reportId) {
    const key = `doctor:${reportId}`;
    const data = await redis.get(key);
    return data ? JSON.parse(data) : null;
  }

  // User activity tracking
  async trackUserActivity(userId, activity) {
    const key = `activity:${userId}`;
    const timestamp = Date.now();
    await redis.zadd(key, timestamp, JSON.stringify(activity));
    await redis.expire(key, 86400); // 24 hours
  }

  async getUserActivity(userId, limit = 10) {
    const key = `activity:${userId}`;
    const activities = await redis.zrevrange(key, 0, limit - 1);
    return activities.map(activity => JSON.parse(activity));
  }
}

module.exports = new CacheService();