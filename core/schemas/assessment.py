from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime

class AssessmentItem(BaseModel):
    item_id: str
    skill_id: str
    concept_id: str
    difficulty: str = "medium"  # easy, medium, hard
    question_type: str = "multiple_choice"
    prompt: str
    code_snippet: Optional[str] = None
    options: List[str]
    correct_answer: str
    explanation: str
    evidence_weight: float = Field(default=1.0, ge=0.1)

class AssessmentAttempt(BaseModel):
    attempt_id: str
    learner_id: str
    goal_id: str
    item_id: str
    skill_id: str
    answer: str
    correct: bool
    response_time_seconds: Optional[float] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class KnowledgeState(BaseModel):
    skill_id: str
    skill_name: str
    demonstrated_score: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    evidence: List[Dict[str, Any]] = Field(default_factory=list)
    last_assessed_at: Optional[str] = None
    trend: str = "stable"  # improving, stable, declining
    status: str = "unknown"  # adequate, needs_improvement, weak, unknown

class GapComparisonItem(BaseModel):
    skill_id: str
    skill_name: str
    self_reported: float
    demonstrated: float
    target: float
    gap: float
    status: str
    is_bottleneck: bool = False

class GapReport(BaseModel):
    goal_id: str
    skill_gaps: Dict[str, float] = Field(default_factory=dict)
    weak_skills: List[str] = Field(default_factory=list)
    needs_improvement_skills: List[str] = Field(default_factory=list)
    adequate_skills: List[str] = Field(default_factory=list)
    unresolved_prerequisites: List[str] = Field(default_factory=list)
    comparison_data: List[GapComparisonItem] = Field(default_factory=list)
