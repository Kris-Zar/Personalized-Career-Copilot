from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from core.schemas.profile import LearnerProfile
from core.schemas.feedback import GoalState, FeedbackEvent
from core.schemas.assessment import KnowledgeState, AssessmentItem, AssessmentAttempt, GapReport
from core.schemas.roadmap import Roadmap, Stage
from core.schemas.resource import Resource, Recommendation

# Profile Requests
class ProfileUpdateRequest(BaseModel):
    name: str = Field(..., description="Learner full name")
    email: Optional[str] = Field(default="", description="Learner email")
    current_role: str = Field(..., description="Current job role or educational background")
    interests: List[str] = Field(default_factory=list, description="Primary technical interests")
    self_reported_skills: Dict[str, float] = Field(default_factory=dict, description="Self-reported proficiency scores (0.0 - 1.0)")
    previous_learning: List[str] = Field(default_factory=list, description="Previous learning experiences")
    weekly_hours: float = Field(default=8.0, description="Available weekly study hours")
    timeline_months: int = Field(default=6, description="Target timeline in months")
    content_preferences: List[str] = Field(default_factory=lambda: ["projects", "interactive", "videos"])

# Goal Requests & Responses
class GoalExtractRequest(BaseModel):
    user_prompt: str = Field(..., description="Natural language career goal description")

class GoalExtractResponse(BaseModel):
    extracted: Dict[str, Any]
    goal_state: GoalState
    source: str = Field(..., description="'gemini' or 'fallback'")
    model: str
    error: Optional[str] = None

class GoalSelectRequest(BaseModel):
    goal_id: str
    target_role: Optional[str] = None
    timeline_months: Optional[int] = None
    weekly_hours: Optional[float] = None

# Assessment Requests
class AttemptSubmitRequest(BaseModel):
    item_id: str
    answer: str

class AssessmentCompleteRequest(BaseModel):
    attempts: Optional[List[AttemptSubmitRequest]] = None

# Roadmap Generation Request
class RoadmapGenerateRequest(BaseModel):
    goal_id: Optional[str] = None
    generation_reason: Optional[str] = "Manual generation request"

# Tutor Chat Request & Response
class TutorChatRequest(BaseModel):
    query: str

class TutorChatResponse(BaseModel):
    reply: str
    source: str
    model: str
    is_adaptation: bool = False
    adaptation_diff: Optional[Dict[str, Any]] = None

# Feedback Request
class FeedbackSubmitRequest(BaseModel):
    message: str
    type: Optional[str] = "difficulty"
    target_id: Optional[str] = "math_prob_stats"
    source: Optional[str] = "chat"

# Dashboard Response
class DashboardResponse(BaseModel):
    learner_name: str
    target_role: str
    timeline_months: int
    weekly_hours: float
    progress_percentage: int
    skills_assessed_count: int
    weak_prerequisites_count: int
    streak_days: int
    current_xp: int
    knowledge_states: List[KnowledgeState]
    gap_report: Optional[GapReport] = None
    current_roadmap: Optional[Roadmap] = None
    chat_history: List[Dict[str, str]]
