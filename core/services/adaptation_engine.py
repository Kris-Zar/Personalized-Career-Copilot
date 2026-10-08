from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from core.schemas.feedback import FeedbackEvent
from core.schemas.roadmap import Roadmap, Stage
from core.schemas.profile import LearnerProfile
from core.schemas.assessment import KnowledgeState, GapReport
from core.services.gap_analyzer import GapAnalyzer
from core.services.roadmap_engine import RoadmapEngine
from core.services.recommender import RecommendationEngine

class AdaptationEngine:
    """
    Continuous adaptation feedback loop engine.
    Ingests conversational or UI feedback events, updates learner model,
    re-plans affected stages, and produces versioned Roadmap N+1 with diffs.
    """
    def __init__(
        self,
        gap_analyzer: GapAnalyzer,
        roadmap_engine: RoadmapEngine,
        recommender: RecommendationEngine
    ):
        self.gap_analyzer = gap_analyzer
        self.roadmap_engine = roadmap_engine
        self.recommender = recommender

    def process_feedback(
        self,
        event: FeedbackEvent,
        profile: LearnerProfile,
        knowledge_states: Dict[str, KnowledgeState],
        current_roadmap: Roadmap
    ) -> Tuple[Roadmap, str]:
        """
        Processes feedback event and generates adapted Roadmap v(N+1) with explanation.
        """
        diff_explanations: List[str] = []
        new_version = current_roadmap.version + 1

        # Signal 1: Difficulty feedback on a skill
        if event.type == "difficulty" or "difficult" in event.message.lower() or "confusing" in event.message.lower():
            target_skill = event.target_id or "math_prob_stats"
            if target_skill in knowledge_states:
                ks = knowledge_states[target_skill]
                ks.status = "weak"
                ks.trend = "declining"
                diff_explanations.append(
                    f"Identified difficulty bottleneck in '{ks.skill_name}'. Injected bite-sized visual exercises and slowed stage progression."
                )

        # Signal 2: Time constraint feedback
        if event.type == "time_constraint" or "30 min" in event.message.lower() or "less time" in event.message.lower():
            profile.weekly_hours = max(3.5, profile.weekly_hours * 0.6)
            diff_explanations.append(
                f"Updated weekly time commitment to {profile.weekly_hours}h/week and resized milestone sprint batches."
            )

        # Signal 3: Preference change
        if "project" in event.message.lower() and "projects" not in profile.content_preferences:
            profile.content_preferences.insert(0, "projects")
            diff_explanations.append("Prioritized hands-on project-based resources across all stages.")

        # Recalculate Gaps
        updated_gap_report = self.gap_analyzer.analyze_gaps(
            goal_id=current_roadmap.goal_id,
            knowledge_states=knowledge_states,
            self_reported_skills=profile.self_reported_skills
        )

        # Generate new Roadmap v(N+1)
        reason_summary = " • ".join(diff_explanations) if diff_explanations else f"Adapted based on learner feedback: '{event.message}'"
        
        new_roadmap = self.roadmap_engine.generate_roadmap(
            goal_id=current_roadmap.goal_id,
            profile=profile,
            knowledge_states=knowledge_states,
            gap_report=updated_gap_report,
            version=new_version,
            generation_reason=f"Adaptation (v{new_version}): {reason_summary}"
        )

        new_roadmap.adaptation_diff = {
            "trigger_message": event.message,
            "version_from": f"v{current_roadmap.version}",
            "version_to": f"v{new_version}",
            "explanation": reason_summary,
            "applied_at": datetime.utcnow().isoformat()
        }

        return new_roadmap, reason_summary
