"""
Database models and schemas
"""
from .chat import ChatMessage, ChatSession, ChatSessionResponse, ChatMessageResponse, ChatHistory
from .knowledge import KnowledgeBase, KnowledgeEntry, SearchResult
from .plant_doctor import PlantDoctorReport

# For MongoDB/Beanie registration
__beanie_models__ = [
    ChatMessage,
    ChatSession, 
    ChatHistory,
    KnowledgeBase,
    KnowledgeEntry,
    PlantDoctorReport
]

__all__ = [
    "ChatMessage",
    "ChatSession",
    "ChatSessionResponse",
    "ChatMessageResponse",
    "ChatHistory",
    "KnowledgeBase",
    "KnowledgeEntry",
    "SearchResult",
    "PlantDoctorReport",
    "__beanie_models__"
]
