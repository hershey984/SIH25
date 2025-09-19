from pydantic import BaseModel, Field
from enum import Enum 
from typing import Optional 

class AgentType(str, Enum):
    CROP_ADVISOR = "crop_advisor"
    PLANT_DOCTOR = "plant_doctor"
    RESOURCE_MANAGER = "resource_manager"
    GENERAL = "general_query"

class SupportingInfo(BaseModel):
    agricultural_context: str = Field(description="Summary of agri data")
    market_context: str = Field(description="Summary of market prices")

class AnalysisResult(BaseModel):
    agent_required: AgentType = Field(description="Name of agent selected for query")
    query_passed: str = Field(description="Query for the agent")
    supporting_info: Optional[SupportingInfo] = Field(None, description="Supporting info")
