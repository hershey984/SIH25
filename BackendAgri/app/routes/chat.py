from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.database import get_db
from app.services.chat_service import chat_service
from app.services.storage_service import storage_service

router = APIRouter(prefix="/chat", tags=["chat"])

# Pydantic models for request/response
class ChatSessionCreate(BaseModel):
    user_id: str
    session_type: str = "general"
    metadata: Optional[Dict[str, Any]] = None

class ChatMessage(BaseModel):
    session_id: str
    message: str
    user_id: str

class PlantDoctorSession(BaseModel):
    user_id: str
    plant_type: Optional[str] = None
    symptoms: str
    image_urls: Optional[List[str]] = None

class KnowledgeSession(BaseModel):
    user_id: str
    topic: str
    category: str

class ChatResponse(BaseModel):
    session_id: str
    user_message: Dict[str, Any]
    bot_response: Dict[str, Any]
    session_type: str

# Chat endpoints
@router.post("/sessions", response_model=Dict[str, str])
async def create_session(session_data: ChatSessionCreate):
    """Create a new chat session"""
    try:
        session_id = await chat_service.create_chat_session(
            user_id=session_data.user_id,
            session_type=session_data.session_type,
            metadata=session_data.metadata
        )
        
        return {"session_id": session_id, "status": "created"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session: {str(e)}"
        )

@router.post("/sessions/plant-doctor", response_model=Dict[str, str])
async def create_plant_doctor_session(session_data: PlantDoctorSession):
    """Create a specialized plant doctor session"""
    try:
        plant_info = {
            "plant_type": session_data.plant_type,
            "symptoms": session_data.symptoms,
            "image_urls": session_data.image_urls or []
        }
        
        session_id = await chat_service.create_plant_doctor_session(
            user_id=session_data.user_id,
            plant_info=plant_info
        )
        
        return {"session_id": session_id, "status": "created", "type": "plant_doctor"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create plant doctor session: {str(e)}"
        )

@router.post("/sessions/knowledge", response_model=Dict[str, str])
async def create_knowledge_session(session_data: KnowledgeSession):
    """Create a specialized knowledge session"""
    try:
        session_id = await chat_service.create_knowledge_session(
            user_id=session_data.user_id,
            topic=session_data.topic,
            category=session_data.category
        )
        
        return {"session_id": session_id, "status": "created", "type": "knowledge"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create knowledge session: {str(e)}"
        )

@router.post("/message", response_model=ChatResponse)
async def send_message(message_data: ChatMessage):
    """Send a message in a chat session"""
    try:
        response = await chat_service.handle_chat_interaction(
            session_id=message_data.session_id,
            user_message=message_data.message,
            user_id=message_data.user_id
        )
        
        return ChatResponse(**response)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send message: {str(e)}"
        )

@router.get("/sessions/{session_id}/history")
async def get_chat_history(session_id: str):
    """Get chat history for a session"""
    try:
        history = await chat_service.get_chat_history(session_id)
        session_info = await chat_service.get_session_info(session_id)
        
        return {
            "session_id": session_id,
            "session_info": session_info,
            "messages": history
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve chat history: {str(e)}"
        )

@router.get("/users/{user_id}/sessions")
async def get_user_sessions(user_id: str, db: Session = Depends(get_db)):
    """Get user's chat sessions"""
    try:
        # Get active sessions from Redis
        active_sessions = await chat_service.get_user_active_sessions(user_id)
        
        # Get archived sessions from database
        archived_sessions = await storage_service.get_user_sessions(db, user_id)
        
        return {
            "user_id": user_id,
            "active_sessions": active_sessions,
            "archived_sessions": archived_sessions
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user sessions: {str(e)}"
        )

@router.post("/sessions/{session_id}/archive")
async def archive_session(session_id: str, user_id: str, db: Session = Depends(get_db)):
    """Archive a chat session to permanent storage"""
    try:
        success = await chat_service.archive_session(db, session_id, user_id)
        
        if success:
            return {"session_id": session_id, "status": "archived"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to archive session"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to archive session: {str(e)}"
        )

@router.get("/sessions/{session_id}/info")
async def get_session_info(session_id: str):
    """Get session metadata"""
    try:
        session_info = await chat_service.get_session_info(session_id)
        
        if not session_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        return session_info
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve session info: {str(e)}"
        )