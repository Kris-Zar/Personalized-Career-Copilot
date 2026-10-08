from typing import Dict, List, Optional
from datetime import datetime
from core.schemas.assessment import KnowledgeState, AssessmentAttempt
from core.schemas.skill_graph import SkillGraph
from core.services.assessment_service import AssessmentService

class KnowledgeStateEngine:
    """
    Translates raw assessment attempts and multi-modal signals into
    calibrated per-skill knowledge estimates using the 5-Tier Evidence Hierarchy.
    """
    def __init__(self, assessment_service: AssessmentService):
        self.assessment_service = assessment_service

    def compute_knowledge_states(
        self,
        skill_graph: SkillGraph,
        attempts: List[AssessmentAttempt],
        self_reported_skills: Optional[Dict[str, float]] = None
    ) -> Dict[str, KnowledgeState]:
        """
        Compute structured KnowledgeState for all skills in graph.
        Distinguishes self-reported claims from demonstrated evidence.
        """
        states: Dict[str, KnowledgeState] = {}
        attempts_by_skill: Dict[str, List[AssessmentAttempt]] = {}

        for att in attempts:
            attempts_by_skill.setdefault(att.skill_id, []).append(att)

        for skill_id, node in skill_graph.nodes.items():
            skill_attempts = attempts_by_skill.get(skill_id, [])
            self_report_val = (self_reported_skills or {}).get(skill_id, 0.0)

            if not skill_attempts:
                # No direct test evidence yet
                states[skill_id] = KnowledgeState(
                    skill_id=skill_id,
                    skill_name=node.name,
                    demonstrated_score=0.0,
                    confidence=0.1,
                    evidence=[{
                        "source": "self_report",
                        "claim": self_report_val,
                        "weight": 0.2
                    }],
                    status="unknown",
                    trend="stable"
                )
                continue

            # Calculate weighted demonstrated score
            total_weight = 0.0
            correct_weight = 0.0
            evidence_records = []

            for att in skill_attempts:
                item = self.assessment_service.get_item(att.item_id)
                weight = item.evidence_weight if item else 1.0
                total_weight += weight
                if att.correct:
                    correct_weight += weight
                evidence_records.append({
                    "item_id": att.item_id,
                    "correct": att.correct,
                    "weight": weight,
                    "timestamp": att.timestamp
                })

            demonstrated_score = (correct_weight / total_weight) if total_weight > 0 else 0.0
            target = node.target_proficiency

            # Calibrate status
            if demonstrated_score >= target:
                status = "adequate"
            elif demonstrated_score >= (target - 0.35):
                status = "needs_improvement"
            else:
                status = "weak"

            confidence = min(0.95, 0.4 + (len(skill_attempts) * 0.25))

            states[skill_id] = KnowledgeState(
                skill_id=skill_id,
                skill_name=node.name,
                demonstrated_score=round(demonstrated_score, 2),
                confidence=round(confidence, 2),
                evidence=evidence_records,
                last_assessed_at=datetime.utcnow().isoformat(),
                trend="improving" if demonstrated_score >= 0.7 else "stable",
                status=status
            )

        return states
