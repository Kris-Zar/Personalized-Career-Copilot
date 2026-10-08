from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime
from core.schemas.resource import Recommendation

class Milestone(BaseModel):
    milestone_id: str
    title: str
    description: str
    success_criteria: List[str] = Field(default_factory=list)
    assessment_ids: List[str] = Field(default_factory=list)
    project_ids: List[str] = Field(default_factory=list)
    completed: bool = False

class Stage(BaseModel):
    stage_id: str
    title: str
    objective: str
    prerequisite_stage_ids: List[str] = Field(default_factory=list)
    estimated_hours: float
    milestone: Milestone
    skill_targets: List[str] = Field(default_factory=list)
    resources: List[Recommendation] = Field(default_factory=list)
    completion_status: str = "not_started"  # not_started, in_progress, completed
    rationale: str

class Roadmap(BaseModel):
    roadmap_id: str
    learner_id: str
    goal_id: str
    version: int = 1
    generated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    generation_reason: str = "Initial personalized roadmap generation"
    total_estimated_hours: float = 0.0
    stages: List[Stage] = Field(default_factory=list)
    rationale: List[str] = Field(default_factory=list)
    adaptation_diff: Optional[Dict[str, str]] = None
