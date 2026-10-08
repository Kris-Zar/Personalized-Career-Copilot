from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime

class FeedbackEvent(BaseModel):
    feedback_id: str
    learner_id: str
    source: str = "chat"  # chat, dashboard, assessment, progress
    type: str = "difficulty"  # difficulty, relevance, pace, preference, knowledge, time_constraint, goal_change
    target_id: Optional[str] = None
    message: str
    extracted_signal: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class GoalState(BaseModel):
    goal_id: str
    target_role: str
    timeline_months: int = 6
    weekly_hours: float = 8.0
    target_proficiency_by_skill: Dict[str, float] = Field(default_factory=dict)
    active: bool = True
