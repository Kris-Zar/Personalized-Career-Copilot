import json
import os
from typing import Dict, List, Optional, Any
from core.schemas.profile import LearnerProfile
from core.schemas.assessment import KnowledgeState, AssessmentAttempt, GapReport
from core.schemas.roadmap import Roadmap
from core.schemas.feedback import FeedbackEvent, GoalState

class InMemoryStore:
    """
    Centralized persistent session state store.
    Provides structured querying, mutation, history preservation, and disk serialization.
    """
    def __init__(self, storage_file: Optional[str] = None):
        self.storage_file = storage_file
        self.profile: Optional[LearnerProfile] = None
        self.goal_state: Optional[GoalState] = None
        self.knowledge_states: Dict[str, KnowledgeState] = {}
        self.assessment_attempts: List[AssessmentAttempt] = []
        self.roadmaps: Dict[int, Roadmap] = {}  # version -> Roadmap
        self.current_roadmap_version: int = 1
        self.gap_report: Optional[GapReport] = None
        self.feedback_events: List[FeedbackEvent] = []
        self.chat_history: List[Dict[str, str]] = []
        self.reset_to_fresh_state()

    def reset_to_fresh_state(self):
        """Initializes a 100% clean, fresh profile for any new user."""
        self.profile = LearnerProfile(
            learner_id="learner_new_user",
            name="",
            email="",
            current_role="",
            interests=[],
            self_reported_skills={},
            previous_learning=[],
            weekly_hours=8.0,
            timeline_months=6,
            content_preferences=["projects", "interactive", "videos"],
            interaction_preferences={"tutor_style": "supportive", "code_examples": True}
        )

        self.goal_state = None
        self.knowledge_states = {}
        self.assessment_attempts = []
        self.roadmaps = {}
        self.current_roadmap_version = 1
        self.gap_report = None
        self.feedback_events = []
        self.chat_history = [
            {
                "role": "assistant",
                "content": "Hello! I am your **XCL PathFinder Career Copilot**. State your target role, available weekly hours, and learning preferences to calibrate your customized learning path!"
            }
        ]

    def reset_to_default_persona(self, persona_name: str = "Alex (ML Engineer Aspirant)"):
        """Initialize with Alex demo persona for 1-click test verification."""
        self.profile = LearnerProfile(
            learner_id="learner_alex_01",
            name="Alex Chen",
            email="alex.chen@example.com",
            current_role="Software Developer",
            interests=["Machine Learning", "Neural Networks", "Applied AI"],
            self_reported_skills={
                "py_core": 0.85,
                "py_data": 0.75,
                "math_linear_algebra": 0.70,
                "math_prob_stats": 0.80,  # Claimed high!
                "math_calculus": 0.60,
                "ml_foundations": 0.50,
                "dl_neural_nets": 0.30,
                "nlp_transformers": 0.20,
                "cv_vision": 0.20,
                "ml_ops": 0.30
            },
            previous_learning=["Completed Python Bootcamp", "Read Data Science with Pandas"],
            weekly_hours=8.0,
            timeline_months=6,
            content_preferences=["projects", "interactive", "videos"],
            interaction_preferences={"tutor_style": "supportive", "code_examples": True}
        )

        self.goal_state = GoalState(
            goal_id="goal_ml_engineer",
            target_role="Machine Learning Engineer",
            timeline_months=6,
            weekly_hours=8.0,
            target_proficiency_by_skill={
                "py_core": 0.85,
                "py_data": 0.80,
                "math_linear_algebra": 0.75,
                "math_prob_stats": 0.80,
                "math_calculus": 0.75,
                "ml_foundations": 0.85,
                "dl_neural_nets": 0.80,
                "nlp_transformers": 0.75,
                "cv_vision": 0.75,
                "ml_ops": 0.75
            },
            active=True
        )

        self.knowledge_states = {}
        self.assessment_attempts = []
        self.roadmaps = {}
        self.current_roadmap_version = 1
        self.gap_report = None
        self.feedback_events = []
        self.chat_history = [
            {
                "role": "assistant",
                "content": "Hello Alex! I am your **XCL PathFinder Career Copilot**. I see your goal is to become an **ML Engineer** within 6 months. Let's run a quick diagnostic knowledge check to calibrate your personalized roadmap!"
            }
        ]

    def add_attempt(self, attempt: AssessmentAttempt):
        self.assessment_attempts.append(attempt)

    def record_feedback(self, event: FeedbackEvent):
        self.feedback_events.append(event)

    def save_roadmap(self, roadmap: Roadmap):
        self.roadmaps[roadmap.version] = roadmap
        self.current_roadmap_version = roadmap.version

    def get_current_roadmap(self) -> Optional[Roadmap]:
        return self.roadmaps.get(self.current_roadmap_version)

    def get_roadmap_by_version(self, version: int) -> Optional[Roadmap]:
        return self.roadmaps.get(version)
