import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from beanie import Document, Indexed
from pydantic import Field
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.services.redis_service import redis_service
from app.services.storage_service import storage_service

# MongoDB Document Models
class ChatMessage(Document):
    """Individual chat message document"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    session_id: Indexed(str)
    message_type: str  # 'user', 'assistant', 'system'
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = {}
    
    class Settings:
        name = "chat_messages"
        indexes = [
            [("session_id", 1), ("timestamp", 1)],
            [("timestamp", -1)]
        ]

class ChatSession(Document):
    """Chat session document"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    user_id: Indexed(str)
    session_type: str = "general"  # 'general', 'plant_doctor', 'knowledge'
    status: str = "active"  # 'active', 'archived', 'deleted'
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    archived_at: Optional[datetime] = None
    metadata: Dict[str, Any] = {}
    message_count: int = 0
    
    class Settings:
        name = "chat_sessions"
        indexes = [
            [("user_id", 1), ("status", 1), ("created_at", -1)],
            [("status", 1), ("updated_at", -1)],
            [("session_type", 1), ("status", 1)]
        ]

class ChatService:
    def __init__(self):
        self.redis_service = redis_service
        self.storage_service = storage_service
    
    async def create_chat_session(self, user_id: str, session_type: str = "general", metadata: Optional[Dict] = None) -> str:
        """Create a new chat session"""
        session_id = str(uuid.uuid4())
        
        # Create session in MongoDB
        session = ChatSession(
            id=session_id,
            user_id=user_id,
            session_type=session_type,
            metadata=metadata or {}
        )
        await session.insert()
        
        # Store session metadata in Redis for quick access
        await self.redis_service.store_session_metadata(
            session_id=session_id,
            user_id=user_id,
            session_type=session_type,
            metadata=metadata
        )
        
        return session_id
    
    async def send_message(self, session_id: str, message_type: str, content: str, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Send a message in a chat session"""
        message = {
            "id": str(uuid.uuid4()),
            "message_type": message_type,  # 'user', 'assistant', 'system'
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
        
        # Store message in MongoDB
        chat_message = ChatMessage(
            session_id=session_id,
            message_type=message_type,
            content=content,
            metadata=metadata or {}
        )
        await chat_message.insert()
        
        # Update session message count and timestamp
        await ChatSession.find_one(ChatSession.id == session_id).update(
            {"$inc": {"message_count": 1}, "$set": {"updated_at": datetime.utcnow()}}
        )
        
        # Store in Redis cache for quick access
        await self.redis_service.store_chat_message(session_id, message)
        
        # Extend session expiry in Redis
        await self.redis_service.extend_session_expiry(session_id)
        
        return message
    
    async def get_chat_history(self, session_id: str, from_cache: bool = True, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get chat history for a session"""
        if from_cache:
            # Try Redis first
            history = await self.redis_service.get_chat_history(session_id)
            if history:
                return history[:limit] if limit else history
        
        # Fallback to MongoDB
        query = ChatMessage.find(ChatMessage.session_id == session_id).sort("+timestamp")
        if limit:
            query = query.limit(limit)
        
        messages = await query.to_list()
        
        # Convert to dict format
        history = []
        for msg in messages:
            history.append({
                "id": msg.id,
                "message_type": msg.message_type,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
                "metadata": msg.metadata
            })
        
        return history
    
    async def get_recent_chat_history(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent chat history (most recent messages first)"""
        messages = await ChatMessage.find(
            ChatMessage.session_id == session_id
        ).sort("-timestamp").limit(limit).to_list()
        
        # Convert to dict format and reverse to get chronological order
        history = []
        for msg in reversed(messages):
            history.append({
                "id": msg.id,
                "message_type": msg.message_type,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
                "metadata": msg.metadata
            })
        
        return history
    
    async def archive_session(self, session_id: str, user_id: str) -> bool:
        """Archive a chat session"""
        try:
            # Update session status to archived in MongoDB
            session = await ChatSession.find_one(ChatSession.id == session_id)
            if not session:
                print(f"Session {session_id} not found")
                return False
            
            session.status = "archived"
            session.archived_at = datetime.utcnow()
            session.updated_at = datetime.utcnow()
            await session.save()
            
            # Clean up from Redis cache
            await self.redis_service.delete_session(session_id, user_id)
            
            print(f"Session {session_id} archived successfully")
            return True
            
        except Exception as e:
            print(f"Error archiving session: {e}")
            return False
    
    async def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session metadata"""
        # Try Redis first
        redis_metadata = await self.redis_service.get_session_metadata(session_id)
        if redis_metadata:
            return redis_metadata
        
        # Fallback to MongoDB
        session = await ChatSession.find_one(ChatSession.id == session_id)
        if session:
            return {
                "session_id": session.id,
                "user_id": session.user_id,
                "session_type": session.session_type,
                "status": session.status,
                "created_at": session.created_at.isoformat(),
                "updated_at": session.updated_at.isoformat(),
                "message_count": session.message_count,
                "metadata": session.metadata
            }
        
        return None
    
    async def get_user_active_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's active sessions with metadata"""
        # Try Redis first for quick access
        try:
            session_ids = await self.redis_service.get_user_active_sessions(user_id)
            sessions = []
            
            for session_id in session_ids:
                metadata = await self.redis_service.get_session_metadata(session_id)
                if metadata:
                    sessions.append(metadata)
            
            if sessions:
                return sessions
        except:
            pass
        
        # Fallback to MongoDB
        db_sessions = await ChatSession.find(
            ChatSession.user_id == user_id,
            ChatSession.status == "active"
        ).sort("-updated_at").to_list()
        
        sessions = []
        for session in db_sessions:
            sessions.append({
                "session_id": session.id,
                "user_id": session.user_id,
                "session_type": session.session_type,
                "status": session.status,
                "created_at": session.created_at.isoformat(),
                "updated_at": session.updated_at.isoformat(),
                "message_count": session.message_count,
                "metadata": session.metadata
            })
        
        return sessions
    
    async def get_user_session_history(self, user_id: str, session_type: Optional[str] = None, 
                                     status: str = "archived", limit: int = 20) -> List[Dict[str, Any]]:
        """Get user's session history from MongoDB"""
        query_filter = {
            "user_id": user_id,
            "status": status
        }
        
        if session_type:
            query_filter["session_type"] = session_type
        
        sessions = await ChatSession.find(query_filter).sort("-updated_at").limit(limit).to_list()
        
        result = []
        for session in sessions:
            result.append({
                "session_id": session.id,
                "user_id": session.user_id,
                "session_type": session.session_type,
                "status": session.status,
                "created_at": session.created_at.isoformat(),
                "updated_at": session.updated_at.isoformat(),
                "archived_at": session.archived_at.isoformat() if session.archived_at else None,
                "message_count": session.message_count,
                "metadata": session.metadata
            })
        
        return result
    
    async def delete_session(self, session_id: str, user_id: str, hard_delete: bool = False) -> bool:
        """Delete a chat session (soft delete by default)"""
        try:
            session = await ChatSession.find_one(ChatSession.id == session_id)
            if not session or session.user_id != user_id:
                return False
            
            if hard_delete:
                # Delete session and all messages
                await ChatMessage.find(ChatMessage.session_id == session_id).delete()
                await session.delete()
            else:
                # Soft delete - mark as deleted
                session.status = "deleted"
                session.updated_at = datetime.utcnow()
                await session.save()
            
            # Clean up from Redis
            await self.redis_service.delete_session(session_id, user_id)
            
            return True
            
        except Exception as e:
            print(f"Error deleting session: {e}")
            return False
    
    async def get_session_statistics(self, user_id: str) -> Dict[str, Any]:
        """Get user's chat session statistics"""
        # Active sessions count
        active_count = await ChatSession.find(
            ChatSession.user_id == user_id,
            ChatSession.status == "active"
        ).count()
        
        # Archived sessions count
        archived_count = await ChatSession.find(
            ChatSession.user_id == user_id,
            ChatSession.status == "archived"
        ).count()
        
        # Total messages count
        user_sessions = await ChatSession.find(
            ChatSession.user_id == user_id
        ).project({"id": 1}).to_list()
        
        session_ids = [session.id for session in user_sessions]
        total_messages = await ChatMessage.find(
            {"session_id": {"$in": session_ids}}
        ).count()
        
        # Session types breakdown
        session_types = await ChatSession.aggregate([
            {"$match": {"user_id": user_id}},
            {"$group": {"_id": "$session_type", "count": {"$sum": 1}}}
        ]).to_list()
        
        types_breakdown = {item["_id"]: item["count"] for item in session_types}
        
        return {
            "active_sessions": active_count,
            "archived_sessions": archived_count,
            "total_messages": total_messages,
            "session_types": types_breakdown
        }
    
    async def simulate_bot_response(self, session_id: str, user_message: str, session_type: str) -> str:
        """Simulate chatbot response (replace with actual AI logic)"""
        if session_type == "plant_doctor":
            return f"Based on your description '{user_message[:50]}...', this could be a common plant issue. Let me analyze further and provide a detailed diagnosis."
        elif session_type == "knowledge":
            return f"I found some relevant information about '{user_message[:30]}...'. Here are the key insights from our knowledge base."
        else:
            return f"Thank you for your message: '{user_message[:50]}...'. How can I assist you further?"
    
    async def handle_chat_interaction(self, session_id: str, user_message: str, user_id: str) -> Dict[str, Any]:
        """Handle complete chat interaction (user message + bot response)"""
        try:
            # Get session info
            session_info = await self.get_session_info(session_id)
            if not session_info:
                raise ValueError(f"Session {session_id} not found")
            
            session_type = session_info.get("session_type", "general")
            
            # Store user message
            user_msg = await self.send_message(
                session_id=session_id,
                message_type="user",
                content=user_message
            )
            
            # Generate bot response (replace with actual AI logic)
            bot_response = await self.simulate_bot_response(session_id, user_message, session_type)
            
            # Store bot response
            bot_msg = await self.send_message(
                session_id=session_id,
                message_type="assistant",
                content=bot_response
            )
            
            return {
                "user_message": user_msg,
                "bot_response": bot_msg,
                "session_id": session_id,
                "session_type": session_type
            }
            
        except Exception as e:
            print(f"Error in chat interaction: {e}")
            raise e
    
    # Specialized methods for different chat types
    async def create_plant_doctor_session(self, user_id: str, plant_info: Dict[str, Any]) -> str:
        """Create specialized plant doctor session"""
        metadata = {
            "plant_type": plant_info.get("plant_type"),
            "symptoms": plant_info.get("symptoms"),
            "images": plant_info.get("image_urls", [])
        }
        
        return await self.create_chat_session(
            user_id=user_id,
            session_type="plant_doctor",
            metadata=metadata
        )
    
    async def create_knowledge_session(self, user_id: str, topic: str, context: Optional[Dict] = None) -> str:
        """Create specialized knowledge base session"""
        metadata = {
            "topic": topic,
            "context": context or {}
        }
        
        return await self.create_chat_session(
            user_id=user_id,
            session_type="knowledge",
            metadata=metadata
        )

# Singleton instance
chat_service = ChatService()