import json
import gzip
from datetime import datetime
from typing import List, Dict, Any, Optional
from google.cloud import storage as gcs
from app.models.chat import ChatSession, ChatMessage
from app.models.knowledge import KnowledgeEntry
from app.models.plant_doctor import PlantDoctorReport
from app.config.settings import settings

class StorageService:
    def __init__(self):
        # Initialize Google Cloud Storage client (replace with your preferred cloud provider)
        if hasattr(settings, 'GCS_BUCKET_NAME') and settings.GCS_BUCKET_NAME:
            try:
                self.gcs_client = gcs.Client(project=settings.GCS_PROJECT_ID)
                self.bucket = self.gcs_client.bucket(settings.GCS_BUCKET_NAME)
                print("✅ Google Cloud Storage initialized")
            except Exception as e:
                self.gcs_client = None
                self.bucket = None
                print(f"Warning: GCS credentials not provided or invalid: {e}")
        else:
            self.gcs_client = None
            self.bucket = None
            print("Warning: Cloud storage credentials not provided. Cloud storage disabled.")
    
    async def save_chat_session(self, session_data: Dict[str, Any], messages: List[Dict[str, Any]]) -> str:
        """Save chat session and messages to MongoDB"""
        try:
            # Create chat session document
            chat_session = ChatSession(
                id=session_data.get("session_id"),
                user_id=session_data["user_id"],
                session_type=session_data.get("session_type", "general"),
                title=session_data.get("title"),
                metadata=session_data.get("metadata")
            )
            
            # Save session to MongoDB
            await chat_session.insert()
            
            # Create and save chat messages
            for msg in messages:
                chat_message = ChatMessage(
                    session_id=str(chat_session.id),
                    message_type=msg["message_type"],
                    content=msg["content"],
                    timestamp=datetime.fromisoformat(msg["timestamp"]) if isinstance(msg["timestamp"], str) else msg["timestamp"],
                    metadata=msg.get("metadata")
                )
                await chat_message.insert()
            
            # Archive to cloud storage if enabled
            if self.bucket:
                await self._archive_session_to_cloud(str(chat_session.id), session_data, messages)
            
            return str(chat_session.id)
            
        except Exception as e:
            print(f"Error saving chat session: {e}")
            raise e
    
    async def _archive_session_to_cloud(self, session_id: str, session_data: Dict[str, Any], messages: List[Dict[str, Any]]):
        """Archive session data to Google Cloud Storage"""
        if not self.bucket:
            return
        
        try:
            # Prepare data for archival
            archive_data = {
                "session_metadata": session_data,
                "messages": messages,
                "archived_at": datetime.utcnow().isoformat()
            }
            
            # Compress and upload to GCS
            json_data = json.dumps(archive_data, default=str, indent=2)
            compressed_data = gzip.compress(json_data.encode('utf-8'))
            
            # Generate GCS blob name
            date_prefix = datetime.utcnow().strftime("%Y/%m/%d")
            blob_name = f"chat_sessions/{date_prefix}/{session_id}.json.gz"
            
            blob = self.bucket.blob(blob_name)
            blob.upload_from_string(
                compressed_data,
                content_type='application/json'
            )
            
            # Update session with cloud storage path
            session = await ChatSession.get(session_id)
            if session:
                session.cloud_storage_path = blob_name
                await session.save()
            
            print(f"Session {session_id} archived to GCS: {blob_name}")
            
        except Exception as e:
            print(f"Error archiving session to cloud: {e}")
    
    async def get_chat_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve chat session with messages from MongoDB"""
        try:
            session = await ChatSession.get(session_id)
            if not session:
                return None
            
            messages = await ChatMessage.find(
                ChatMessage.session_id == session_id
            ).sort(+ChatMessage.timestamp).to_list()
            
            return {
                "session": {
                    "id": str(session.id),
                    "user_id": session.user_id,
                    "session_type": session.session_type,
                    "title": session.title,
                    "created_at": session.created_at.isoformat(),
                    "updated_at": session.updated_at.isoformat(),
                    "metadata": session.metadata
                },
                "messages": [
                    {
                        "id": str(msg.id),
                        "message_type": msg.message_type,
                        "content": msg.content,
                        "timestamp": msg.timestamp.isoformat(),
                        "metadata": msg.metadata
                    } for msg in messages
                ]
            }
        except Exception as e:
            print(f"Error retrieving chat session: {e}")
            return None
    
    async def get_user_sessions(self, user_id: str, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Get user's chat sessions (without messages) from MongoDB"""
        try:
            sessions = await ChatSession.find(
                ChatSession.user_id == user_id
            ).sort(-ChatSession.updated_at).skip(offset).limit(limit).to_list()
            
            return [
                {
                    "id": str(session.id),
                    "session_type": session.session_type,
                    "title": session.title,
                    "created_at": session.created_at.isoformat(),
                    "updated_at": session.updated_at.isoformat(),
                    "metadata": session.metadata
                } for session in sessions
            ]
        except Exception as e:
            print(f"Error retrieving user sessions: {e}")
            return []
    
    async def save_knowledge_entry(self, knowledge_data: Dict[str, Any]) -> str:
        """Save knowledge entry to MongoDB"""
        try:
            entry = KnowledgeEntry(
                title=knowledge_data["title"],
                content=knowledge_data["content"],
                category=knowledge_data["category"],
                tags=knowledge_data.get("tags"),
                author_id=knowledge_data.get("author_id")
            )
            
            await entry.insert()
            
            # Archive to cloud if needed
            if self.bucket and knowledge_data.get("archive_to_cloud", False):
                await self._archive_knowledge_to_cloud(str(entry.id), knowledge_data)
            
            return str(entry.id)
            
        except Exception as e:
            print(f"Error saving knowledge entry: {e}")
            raise e
    
    async def save_plant_doctor_report(self, report_data: Dict[str, Any]) -> str:
        """Save plant doctor report to MongoDB"""
        try:
            report = PlantDoctorReport(
                user_id=report_data["user_id"],
                plant_type=report_data.get("plant_type"),
                symptoms=report_data["symptoms"],
                diagnosis=report_data.get("diagnosis"),
                treatment=report_data.get("treatment"),
                confidence_score=report_data.get("confidence_score"),
                image_urls=report_data.get("image_urls", []),
                status=report_data.get("status", "pending")
            )
            
            await report.insert()
            
            return str(report.id)
            
        except Exception as e:
            print(f"Error saving plant doctor report: {e}")
            raise e
    
    async def _archive_knowledge_to_cloud(self, entry_id: str, knowledge_data: Dict[str, Any]):
        """Archive knowledge entry to Google Cloud Storage"""
        if not self.bucket:
            return
        
        try:
            date_prefix = datetime.utcnow().strftime("%Y/%m/%d")
            blob_name = f"knowledge_entries/{date_prefix}/{entry_id}.json"
            
            blob = self.bucket.blob(blob_name)
            blob.upload_from_string(
                json.dumps(knowledge_data, default=str, indent=2),
                content_type='application/json'
            )
            
            # Update entry with cloud storage path
            entry = await KnowledgeEntry.get(entry_id)
            if entry:
                entry.cloud_storage_path = blob_name
                await entry.save()
            
        except Exception as e:
            print(f"Error archiving knowledge to cloud: {e}")

    async def get_knowledge_entries(self, category: Optional[str] = None, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Get knowledge entries with optional filtering"""
        try:
            query = KnowledgeEntry.find()
            
            if category:
                query = query.find(KnowledgeEntry.category == category)
            
            entries = await query.sort(-KnowledgeEntry.created_at).skip(offset).limit(limit).to_list()
            
            return [
                {
                    "id": str(entry.id),
                    "title": entry.title,
                    "category": entry.category,
                    "tags": entry.tags,
                    "created_at": entry.created_at.isoformat(),
                    "author_id": entry.author_id
                } for entry in entries
            ]
        except Exception as e:
            print(f"Error retrieving knowledge entries: {e}")
            return []

    async def get_plant_doctor_reports(self, user_id: Optional[str] = None, status: Optional[str] = None, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Get plant doctor reports with optional filtering"""
        try:
            query = PlantDoctorReport.find()
            
            if user_id:
                query = query.find(PlantDoctorReport.user_id == user_id)
            if status:
                query = query.find(PlantDoctorReport.status == status)
            
            reports = await query.sort(-PlantDoctorReport.created_at).skip(offset).limit(limit).to_list()
            
            return [
                {
                    "id": str(report.id),
                    "user_id": report.user_id,
                    "plant_type": report.plant_type,
                    "symptoms": report.symptoms,
                    "diagnosis": report.diagnosis,
                    "status": report.status,
                    "created_at": report.created_at.isoformat(),
                    "confidence_score": report.confidence_score
                } for report in reports
            ]
        except Exception as e:
            print(f"Error retrieving plant doctor reports: {e}")
            return []

# Singleton instance
storage_service = StorageService()