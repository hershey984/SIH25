from beanie import Document, Indexed
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from pymongo import IndexModel, TEXT
import uuid

class KnowledgeEntry(Document):
    """Knowledge base entry document for MongoDB"""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    title: Indexed(str)  # Indexed for text search
    content: str
    category: Indexed(str)  # Indexed for category filtering
    tags: Optional[List[str]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    author_id: Optional[str] = None
    cloud_storage_path: Optional[str] = None
    view_count: int = 0
    is_published: bool = True
    
    class Settings:
        name = "knowledge_entries"
        indexes = [
            IndexModel([("title", TEXT), ("content", TEXT)]),  # Text search index
            IndexModel([("category", 1), ("created_at", -1)]),
            IndexModel([("tags", 1)]),
            IndexModel([("author_id", 1)]),
            IndexModel([("is_published", 1), ("created_at", -1)])
        ]

class KnowledgeBase(Document):
    """Knowledge base collection metadata"""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    name: str
    description: Optional[str] = None
    categories: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    entry_count: int = 0
    
    class Settings:
        name = "knowledge_bases"

# Pydantic models for API
class KnowledgeEntryCreate(BaseModel):
    """Request model for creating knowledge entries"""
    title: str
    content: str
    category: str
    tags: Optional[List[str]] = None
    author_id: Optional[str] = None
    is_published: bool = True

class KnowledgeEntryUpdate(BaseModel):
    """Request model for updating knowledge entries"""
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    is_published: Optional[bool] = None

class KnowledgeEntryResponse(BaseModel):
    """Response model for knowledge entries"""
    id: str
    title: str
    content: str
    category: str
    tags: Optional[List[str]]
    created_at: datetime
    updated_at: datetime
    author_id: Optional[str]
    view_count: int
    is_published: bool

class SearchResult(BaseModel):
    """Search result model"""
    id: str
    title: str
    content_preview: str  # Truncated content
    category: str
    tags: Optional[List[str]]
    relevance_score: Optional[float] = None
    created_at: datetime