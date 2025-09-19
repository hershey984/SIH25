from beanie import Document, Indexed
from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, List, Dict, Any
from pymongo import IndexModel
import uuid

class PlantDoctorReport(Document):
    """Plant doctor diagnosis report document for MongoDB"""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    user_id: Indexed(str)  # Indexed for user queries
    plant_type: Optional[str] = None
    symptoms: str
    diagnosis: Optional[str] = None
    treatment: Optional[str] = None
    confidence_score: Optional[int] = Field(None, ge=0, le=100)  # 0-100 validation
    image_urls: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    status: Indexed(str) = Field(default="pending")  # pending, diagnosed, reviewed, completed
    cloud_storage_path: Optional[str] = None
    
    # Additional useful fields
    doctor_id: Optional[str] = None  # ID of the plant doctor who made the diagnosis
    priority: Optional[str] = Field(default="normal")  # low, normal, high, urgent
    tags: List[str] = []  # For categorization and filtering
    metadata: Dict[str, Any] = {}  # For storing additional flexible data
    notes: Optional[str] = None  # Internal notes or comments
    follow_up_required: bool = False
    follow_up_date: Optional[datetime] = None
    
    # Validation
    @validator('status')
    def validate_status(cls, v):
        valid_statuses = ['pending', 'diagnosed', 'reviewed', 'completed']
        if v not in valid_statuses:
            raise ValueError(f'Status must be one of: {valid_statuses}')
        return v
    
    @validator('priority')
    def validate_priority(cls, v):
        if v is not None:
            valid_priorities = ['low', 'normal', 'high', 'urgent']
            if v not in valid_priorities:
                raise ValueError(f'Priority must be one of: {valid_priorities}')
        return v
    
    @validator('symptoms')
    def validate_symptoms(cls, v):
        if not v or len(v.strip()) < 10:
            raise ValueError('Symptoms description must be at least 10 characters long')
        return v.strip()
    
    # Update timestamp on save
    def save(self, *args, **kwargs):
        self.updated_at = datetime.utcnow()
        return super().save(*args, **kwargs)
    
    class Settings:
        name = "plant_doctor_reports"  # Collection name
        
        # Define compound indexes for better query performance
        indexes = [
            # Compound index for user queries by status and date
            [("user_id", 1), ("status", 1), ("created_at", -1)],
            # Index for diagnosis queries
            [("plant_type", 1), ("status", 1)],
            # Index for doctor assignments
            [("doctor_id", 1), ("status", 1)],
            # Text search index for symptoms and diagnosis
            [("symptoms", "text"), ("diagnosis", "text")],
            # TTL index for cleanup (optional - removes completed reports after 1 year)
            IndexModel([("created_at", 1)], expireAfterSeconds=31536000, partialFilterExpression={"status": "completed"})
        ]

# Example usage and helper methods
class PlantDoctorReportService:
    """Service class for common PlantDoctorReport operations"""
    
    @staticmethod
    async def create_report(user_id: str, plant_type: str, symptoms: str, image_urls: List[str] = None) -> PlantDoctorReport:
        """Create a new plant doctor report"""
        report = PlantDoctorReport(
            user_id=user_id,
            plant_type=plant_type,
            symptoms=symptoms,
            image_urls=image_urls or []
        )
        await report.insert()
        return report
    
    @staticmethod
    async def get_user_reports(user_id: str, status: Optional[str] = None) -> List[PlantDoctorReport]:
        """Get all reports for a specific user, optionally filtered by status"""
        query = {"user_id": user_id}
        if status:
            query["status"] = status
        
        return await PlantDoctorReport.find(query).sort("-created_at").to_list()
    
    @staticmethod
    async def update_diagnosis(report_id: str, diagnosis: str, treatment: str, 
                             confidence_score: int, doctor_id: str) -> Optional[PlantDoctorReport]:
        """Update a report with diagnosis information"""
        report = await PlantDoctorReport.get(report_id)
        if report:
            report.diagnosis = diagnosis
            report.treatment = treatment
            report.confidence_score = confidence_score
            report.doctor_id = doctor_id
            report.status = "diagnosed"
            await report.save()
        return report
    
    @staticmethod
    async def search_reports(query: str, plant_type: Optional[str] = None) -> List[PlantDoctorReport]:
        """Search reports using text search on symptoms and diagnosis"""
        search_filter = {"$text": {"$search": query}}
        if plant_type:
            search_filter["plant_type"] = plant_type
            
        return await PlantDoctorReport.find(search_filter).to_list()