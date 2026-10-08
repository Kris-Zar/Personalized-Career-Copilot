from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any

class Resource(BaseModel):
    resource_id: str
    title: str
    resource_type: str = "course"  # course, video, article, book, exercise, project
    provider: str
    url: str
    skills_covered: List[str] = Field(default_factory=list)
    prerequisite_skill_ids: List[str] = Field(default_factory=list)
    difficulty: str = "intermediate"  # beginner, intermediate, advanced
    estimated_hours: float = Field(default=5.0)
    format: str = "video"  # hands-on, video, reading, interactive
    quality_score: float = Field(default=4.7, ge=0.0, le=5.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class Recommendation(BaseModel):
    resource_id: str
    title: str
    resource_type: str
    provider: str
    url: str
    relevance_score: float = Field(default=0.9, ge=0.0, le=1.0)
    matched_skills: List[str] = Field(default_factory=list)
    reason: str
    estimated_effort_hours: float
    prerequisite_status: str = "met"  # met, unmet
    priority: int = 1
