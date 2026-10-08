import json
import os
from typing import Dict, List, Optional
from core.schemas.resource import Resource, Recommendation
from core.schemas.profile import LearnerProfile
from core.schemas.assessment import KnowledgeState

class RecommendationEngine:
    """
    Multi-signal ranking engine for matching curated courses, projects,
    and interactive exercises against learner gaps and constraints.
    """
    def __init__(self, catalog_path: str = "data/resources/resources_catalog.json"):
        self.catalog_path = catalog_path
        self.resources: Dict[str, Resource] = {}
        self._load_catalog()

    def _load_catalog(self):
        if not os.path.exists(self.catalog_path):
            return
        try:
            with open(self.catalog_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    res = Resource(**item)
                    self.resources[res.resource_id] = res
        except Exception as e:
            print(f"Error loading resource catalog: {e}")

    def get_resource(self, resource_id: str) -> Optional[Resource]:
        return self.resources.get(resource_id)

    def recommend_for_skill(
        self,
        skill_id: str,
        knowledge_states: Dict[str, KnowledgeState],
        profile: LearnerProfile,
        max_results: int = 3
    ) -> List[Recommendation]:
        """
        Rank and return top resources specifically addressing a target skill.
        """
        candidates = [
            res for res in self.resources.values()
            if skill_id in res.skills_covered
        ]

        scored_recommendations: List[Recommendation] = []

        for res in candidates:
            score = 0.0
            reasons = []

            # 1. Skill Gap Match
            score += 0.4
            reasons.append(f"Directly covers target skill '{skill_id}'")

            # 2. Prerequisite Check
            prereq_met = True
            for prereq in res.prerequisite_skill_ids:
                ks = knowledge_states.get(prereq)
                if not ks or ks.status in ["weak", "unknown"]:
                    prereq_met = False
                    break

            if prereq_met:
                score += 0.25
                prereq_status = "met"
            else:
                score += 0.05
                prereq_status = "unmet"
                reasons.append("Contains unmet prerequisites")

            # 3. Format / Preference Fit
            if res.format in profile.content_preferences:
                score += 0.15
                reasons.append(f"Matches preferred format ({res.format})")

            # 4. Quality Score
            quality_boost = (res.quality_score / 5.0) * 0.15
            score += quality_boost

            # 5. Time fit
            if res.estimated_hours <= (profile.weekly_hours * 1.5):
                score += 0.05

            relevance = min(0.99, max(0.1, round(score, 2)))
            reason_text = " • ".join(reasons)

            rec = Recommendation(
                resource_id=res.resource_id,
                title=res.title,
                resource_type=res.resource_type,
                provider=res.provider,
                url=res.url,
                relevance_score=relevance,
                matched_skills=res.skills_covered,
                reason=reason_text,
                estimated_effort_hours=res.estimated_hours,
                prerequisite_status=prereq_status,
                priority=1
            )
            scored_recommendations.append(rec)

        # Sort descending by relevance score
        scored_recommendations.sort(key=lambda r: (r.prerequisite_status == "met", r.relevance_score), reverse=True)
        return scored_recommendations[:max_results]
