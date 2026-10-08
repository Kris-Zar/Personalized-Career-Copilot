from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime

class LearnerProfile(BaseModel):
    learner_id: str = Field(default="learner_001")
    name: str = Field(default="Learner")
    email: Optional[str] = None
    current_role: Optional[str] = "Student / Professional"
    interests: List[str] = Field(default_factory=list)
    # self-reported proficiency mapping (skill_id -> 0.0 to 1.0)
    self_reported_skills: Dict[str, float] = Field(default_factory=dict)
    previous_learning: List[str] = Field(default_factory=list)
    weekly_hours: float = Field(default=8.0)
    timeline_months: int = Field(default=6)
    content_preferences: List[str] = Field(default_factory=lambda: ["projects", "videos", "exercises"])
    interaction_preferences: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
