import redis
import json
import pickle
from typing import Optional, List, Dict, Any
from app.config.settings import settings

class RedisService:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            decode_responses=False  # We'll handle encoding manually
        )
    
    def get_session_key(self, session_id: str) -> str:
        """Generate Redis key for chat session"""
        return f"chat_session:{session_id}"
    
    def get_user_sessions_key(self, user_id: str) -> str:
        """Generate Redis key for user's active sessions"""
        return f"user_sessions:{user_id}"
    
    async def store_chat_message(self, session_id: str, message: Dict[str, Any]) -> bool:
        """Store a single chat message in Redis session cache"""
        try:
            session_key = self.get_session_key(session_id)
            
            # Serialize message
            serialized_message = json.dumps(message, default=str)
            
            # Add to session's message list
            self.redis_client.lpush(session_key, serialized_message)
            
            # Set expiration
            self.redis_client.expire(session_key, settings.SESSION_EXPIRE_SECONDS)
            
            # Trim to keep only recent messages
            self.redis_client.ltrim(session_key, 0, settings.CHAT_HISTORY_LIMIT - 1)
            
            return True
        except Exception as e:
            print(f"Error storing chat message: {e}")
            return False
    
    async def get_chat_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Retrieve chat history from Redis"""
        try:
            session_key = self.get_session_key(session_id)
            messages = self.redis_client.lrange(session_key, 0, -1)
            
            # Deserialize messages (reverse to get chronological order)
            chat_history = []
            for msg in reversed(messages):
                try:
                    message = json.loads(msg.decode('utf-8'))
                    chat_history.append(message)
                except json.JSONDecodeError:
                    continue
            
            return chat_history
        except Exception as e:
            print(f"Error retrieving chat history: {e}")
            return []
    
    async def store_session_metadata(self, session_id: str, user_id: str, session_type: str, metadata: Optional[Dict] = None) -> bool:
        """Store session metadata"""
        try:
            session_meta_key = f"session_meta:{session_id}"
            session_data = {
                "session_id": session_id,
                "user_id": user_id,
                "session_type": session_type,
                "created_at": str(datetime.utcnow()),
                "metadata": metadata or {}
            }
            
            serialized_data = json.dumps(session_data, default=str)
            self.redis_client.set(session_meta_key, serialized_data, ex=settings.SESSION_EXPIRE_SECONDS)
            
            # Add to user's session list
            user_sessions_key = self.get_user_sessions_key(user_id)
            self.redis_client.sadd(user_sessions_key, session_id)
            self.redis_client.expire(user_sessions_key, settings.SESSION_EXPIRE_SECONDS)
            
            return True
        except Exception as e:
            print(f"Error storing session metadata: {e}")
            return False
    
    async def get_session_metadata(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session metadata"""
        try:
            session_meta_key = f"session_meta:{session_id}"
            data = self.redis_client.get(session_meta_key)
            if data:
                return json.loads(data.decode('utf-8'))
            return None
        except Exception as e:
            print(f"Error retrieving session metadata: {e}")
            return None
    
    async def get_user_active_sessions(self, user_id: str) -> List[str]:
        """Get all active session IDs for a user"""
        try:
            user_sessions_key = self.get_user_sessions_key(user_id)
            sessions = self.redis_client.smembers(user_sessions_key)
            return [s.decode('utf-8') for s in sessions]
        except Exception as e:
            print(f"Error retrieving user sessions: {e}")
            return []
    
    async def extend_session_expiry(self, session_id: str) -> bool:
        """Extend session expiry time"""
        try:
            session_key = self.get_session_key(session_id)
            session_meta_key = f"session_meta:{session_id}"
            
            self.redis_client.expire(session_key, settings.SESSION_EXPIRE_SECONDS)
            self.redis_client.expire(session_meta_key, settings.SESSION_EXPIRE_SECONDS)
            return True
        except Exception as e:
            print(f"Error extending session expiry: {e}")
            return False
    
    async def delete_session(self, session_id: str, user_id: str) -> bool:
        """Delete session from cache"""
        try:
            session_key = self.get_session_key(session_id)
            session_meta_key = f"session_meta:{session_id}"
            user_sessions_key = self.get_user_sessions_key(user_id)
            
            self.redis_client.delete(session_key)
            self.redis_client.delete(session_meta_key)
            self.redis_client.srem(user_sessions_key, session_id)
            
            return True
        except Exception as e:
            print(f"Error deleting session: {e}")
            return False

# Singleton instance
redis_service = RedisService()