from typing import Dict, List, Optional
from core.schemas.assessment import GapReport, GapComparisonItem, KnowledgeState
from core.schemas.skill_graph import SkillGraph
from core.services.graph_service import GraphService

class GapAnalyzer:
    """
    Identifies competency deficits, prerequisite bottlenecks,
    and self-reported vs. demonstrated knowledge discrepancies.
    """
    def __init__(self, graph_service: GraphService):
        self.graph_service = graph_service

    def analyze_gaps(
        self,
        goal_id: str,
        knowledge_states: Dict[str, KnowledgeState],
        self_reported_skills: Optional[Dict[str, float]] = None
    ) -> GapReport:
        graph = self.graph_service.get_graph(goal_id)
        if not graph:
            return GapReport(goal_id=goal_id)

        skill_gaps: Dict[str, float] = {}
        weak_skills: List[str] = []
        needs_improvement_skills: List[str] = []
        adequate_skills: List[str] = []
        comparison_data: List[GapComparisonItem] = []

        topo_order = self.graph_service.topological_sort(goal_id)

        for skill_id in topo_order:
            node = graph.nodes.get(skill_id)
            if not node:
                continue

            ks = knowledge_states.get(skill_id)
            demonstrated = ks.demonstrated_score if ks else 0.0
            self_reported = (self_reported_skills or {}).get(skill_id, 0.0)
            target = node.target_proficiency
            gap = max(0.0, target - demonstrated)
            skill_gaps[skill_id] = round(gap, 2)

            status = ks.status if ks else "unknown"

            if status == "weak":
                weak_skills.append(skill_id)
            elif status == "needs_improvement":
                needs_improvement_skills.append(skill_id)
            elif status == "adequate":
                adequate_skills.append(skill_id)

        # Identify prerequisite bottlenecks:
        # A skill is a bottleneck if it is weak/unresolved AND required as a prerequisite by downstream skills
        unresolved_prerequisites: List[str] = []
        for skill_id in weak_skills + needs_improvement_skills:
            # Check if any other node has this as a prerequisite
            is_prereq_for_other = any(
                skill_id in other_node.prerequisite_skill_ids
                for other_node in graph.nodes.values()
            )
            if is_prereq_for_other:
                unresolved_prerequisites.append(skill_id)

        # Build comparison items
        for skill_id, node in graph.nodes.items():
            ks = knowledge_states.get(skill_id)
            demonstrated = ks.demonstrated_score if ks else 0.0
            self_reported = (self_reported_skills or {}).get(skill_id, 0.0)
            target = node.target_proficiency
            gap = skill_gaps.get(skill_id, 0.0)
            status = ks.status if ks else "unknown"

            comparison_data.append(
                GapComparisonItem(
                    skill_id=skill_id,
                    skill_name=node.name,
                    self_reported=round(self_reported, 2),
                    demonstrated=round(demonstrated, 2),
                    target=round(target, 2),
                    gap=round(gap, 2),
                    status=status,
                    is_bottleneck=(skill_id in unresolved_prerequisites)
                )
            )

        return GapReport(
            goal_id=goal_id,
            skill_gaps=skill_gaps,
            weak_skills=weak_skills,
            needs_improvement_skills=needs_improvement_skills,
            adequate_skills=adequate_skills,
            unresolved_prerequisites=unresolved_prerequisites,
            comparison_data=comparison_data
        )
