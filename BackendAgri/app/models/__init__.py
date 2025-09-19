"""
Database models and schemas
"""
from .chat import ChatMessage, ChatSession, ChatResponse, ChatHistory
from .knowledge import KnowledgeBase, KnowledgeEntry, SearchResult
from .plant_doctor import PlantDiagnosis, PlantImage, DiagnosisResult, PlantDisease

# For MongoDB/Beanie registration
__beanie_models__ = [
    ChatMessage,
    ChatSession, 
    ChatHistory,
    KnowledgeBase,
    KnowledgeEntry,
    PlantDiagnosis,
    PlantImage,
    DiagnosisResult,
    PlantDisease
]

__all__ = [
    "ChatMessage", "ChatSession", "ChatResponse", "ChatHistory",
    "KnowledgeBase", "KnowledgeEntry", "SearchResult", 
    "PlantDiagnosis", "PlantImage", "DiagnosisResult", "PlantDisease",
    "__beanie_models__"
]