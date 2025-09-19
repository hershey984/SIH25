from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.services.storage_service import storage_service

router = APIRouter(prefix="/storage", tags=["storage"])

# Pydantic models
class KnowledgeEntryCreate(BaseModel):
    title: str
    content: str
    category: str
    tags: Optional[List[str]] = None
    author_id: Optional[str] = None
    archive_to_cloud: bool = False

class PlantDoctorReportCreate(BaseModel):
    user_id: str
    plant_type: Optional[str] = None
    symptoms: str
    diagnosis: Optional[str] = None
    treatment: Optional[str] = None
    confidence_score: Optional[int] = None
    image_urls: Optional[List[str]] = None
    status: str = "pending"

class ChatSessionCreate(BaseModel):
    user_id: str
    session_type: str = "general"
    title: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class ChatMessageCreate(BaseModel):
    message_type: str  # 'user', 'assistant', 'system'
    content: str
    timestamp: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

# Knowledge base endpoints
@router.post("/knowledge", response_model=Dict[str, str])
async def create_knowledge_entry(knowledge_data: KnowledgeEntryCreate):
    """Create a new knowledge base entry"""
    try:
        entry_data = knowledge_data.dict()
        entry_id = await storage_service.save_knowledge_entry(entry_data)
        
        return {"entry_id": entry_id, "status": "created"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create knowledge entry: {str(e)}"
        )

@router.get("/knowledge")
async def get_knowledge_entries(
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(50, ge=1, le=100, description="Number of entries to return"),
    offset: int = Query(0, ge=0, description="Number of entries to skip")
):
    """Get knowledge entries with optional filtering"""
    try:
        entries = await storage_service.get_knowledge_entries(category, limit, offset)
        return {
            "entries": entries,
            "limit": limit,
            "offset": offset,
            "category": category
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve knowledge entries: {str(e)}"
        )

@router.post("/plant-doctor-reports", response_model=Dict[str, str])
async def create_plant_doctor_report(report_data: PlantDoctorReportCreate):
    """Create a new plant doctor report"""
    try:
        report_dict = report_data.dict()
        report_id = await storage_service.save_plant_doctor_report(report_dict)
        
        return {"report_id": report_id, "status": "created"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create plant doctor report: {str(e)}"
        )

@router.get("/plant-doctor-reports")
async def get_plant_doctor_reports(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    limit: int = Query(50, ge=1, le=100, description="Number of reports to return"),
    offset: int = Query(0, ge=0, description="Number of reports to skip")
):
    """Get plant doctor reports with optional filtering"""
    try:
        reports = await storage_service.get_plant_doctor_reports(user_id, status_filter, limit, offset)
        return {
            "reports": reports,
            "limit": limit,
            "offset": offset,
            "user_id": user_id,
            "status": status_filter
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve plant doctor reports: {str(e)}"
        )

@router.get("/sessions/{session_id}")
async def get_stored_session(session_id: str):
    """Retrieve a stored chat session"""
    try:
        session_data = await storage_service.get_chat_session(session_id)
        
        if not session_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        return session_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve session: {str(e)}"
        )

@router.get("/users/{user_id}/sessions")
async def get_user_stored_sessions(
    user_id: str, 
    limit: int = Query(50, ge=1, le=100, description="Number of sessions to return"), 
    offset: int = Query(0, ge=0, description="Number of sessions to skip")
):
    """Get user's stored sessions"""
    try:
        sessions = await storage_service.get_user_sessions(user_id, limit, offset)
        
        return {
            "user_id": user_id,
            "sessions": sessions,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user sessions: {str(e)}"
        )

@router.post("/sessions", response_model=Dict[str, str])
async def create_chat_session(
    session_data: ChatSessionCreate,
    messages: List[ChatMessageCreate]
):
    """Create a new chat session with messages"""
    try:
        session_dict = session_data.dict()
        messages_dict = [msg.dict() for msg in messages]
        
        # Add timestamp to messages if not provided
        from datetime import datetime
        for msg in messages_dict:
            if not msg.get("timestamp"):
                msg["timestamp"] = datetime.utcnow().isoformat()
        
        session_id = await storage_service.save_chat_session(session_dict, messages_dict)
        
        return {"session_id": session_id, "status": "created"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create chat session: {str(e)}"
        )

# Health check for storage service
@router.get("/health")
async def storage_health_check():
    """Check storage service health"""
    try:
        # You could add more comprehensive health checks here
        # like testing database connectivity, cloud storage, etc.
        return {
            "status": "healthy",
            "storage_service": "operational",
            "cloud_storage": "available" if storage_service.bucket else "disabled"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Storage service health check failed: {str(e)}"
        )