from beanie import Document, Indexed
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any, List
from pymongo import IndexModel
import uuid

class ChatSession(Document):
    """Chat session document for MongoDB"""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    user_id: Indexed(str)  # Indexed for faster queries
    session_type: str  # 'general', 'plant_doctor', 'knowledge'
    title: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None
    cloud_storage_path: Optional[str] = None  # Path for archived data
    
    class Settings:
        name = "chat_sessions"
        indexes = [
            IndexModel([("user_id", 1), ("updated_at", -1)]),  # Compound index for user queries
            IndexModel([("session_type", 1)]),
            IndexModel([("created_at", -1)])
        ]

class ChatMessage(Document):
    """Chat message document for MongoDB"""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    session_id: Indexed(str)  # Reference to chat session
    message_type: str  # 'user', 'assistant', 'system'
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None
    
    class Settings:
        name = "chat_messages"
        indexes = [
            IndexModel([("session_id", 1), ("timestamp", 1)]),  # For retrieving session messages
            IndexModel([("message_type", 1)]),
            IndexModel([("timestamp", -1)])
        ]

# Pydantic models for API requests/responses
class ChatSessionCreate(BaseModel):
    """Request model for creating chat sessions"""
    user_id: str
    session_type: str = "general"
    title: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class ChatSessionResponse(BaseModel):
    """Response model for chat sessions"""
    id: str
    user_id: str
    session_type: str
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    metadata: Optional[Dict[str, Any]]

class ChatMessageCreate(BaseModel):
    """Request model for creating chat messages"""
    session_id: str
    message_type: str
    content: str
    metadata: Optional[Dict[str, Any]] = None

class ChatMessageResponse(BaseModel):
    """Response model for chat messages"""
    id: str
    session_id: str
    message_type: str
    content: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]]

class ChatHistory(BaseModel):
    """Complete chat session with messages"""
    session: ChatSessionResponse
    messages: List[ChatMessageResponse]