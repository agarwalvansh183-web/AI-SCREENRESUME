"""
Pydantic Schemas for AI Resume Screening System
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class JobCreate(BaseModel):
    title: str = Field(..., description="Title of job opening")
    department: str = Field(default="Engineering", description="Department name")
    experience_level: str = Field(default="Mid-Level (3-5 yrs)", description="Seniority level")
    min_experience_years: int = Field(default=2, ge=0, description="Minimum years of experience")
    required_skills: List[str] = Field(..., description="List of must-have technical skills")
    preferred_skills: List[str] = Field(default_factory=list, description="Bonus / nice-to-have skills")
    description: str = Field(..., description="Full job description")


class ScreenTextRequest(BaseModel):
    job_id: int
    resume_text: str
    candidate_name: Optional[str] = None
    email: Optional[str] = None
    gemini_api_key: Optional[str] = None


class StatusUpdateRequest(BaseModel):
    status: str
    notes: Optional[str] = None


class TestApiKeyRequest(BaseModel):
    api_key: str
