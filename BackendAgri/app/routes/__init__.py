"""
API routes and endpoints
"""
from fastapi import APIRouter
from .chat import router as chat_router
from .storage import router as storage_router

# Main API router
api_router = APIRouter(prefix="/api/v1")

# Include all route modules
api_router.include_router(
    chat_router, 
    prefix="/chat", 
    tags=["Chat & AI Assistant"]
)

api_router.include_router(
    storage_router, 
    prefix="/storage", 
    tags=["File Storage & Management"]
)

__all__ = ["api_router"]