from typing import Dict, List, Optional
from datetime import datetime
import uuid
from core.schemas.roadmap import Roadmap, Stage, Milestone
from core.schemas.profile import LearnerProfile
from core.schemas.assessment import GapReport, KnowledgeState
from core.schemas.skill_graph import SkillGraph
from core.services.graph_service import GraphService
from core.services.recommender import RecommendationEngine

class RoadmapEngine:
    """
    Constructs deterministic, prerequisite-ordered, milestone-driven roadmaps
    grounded in the competency graph and learner constraints.
    """
    def __init__(self, graph_service: GraphService, recommender: RecommendationEngine):
        self.graph_service = graph_service
        self.recommender = recommender

    def generate_roadmap(
        self,
        goal_id: str,
        profile: LearnerProfile,
        knowledge_states: Dict[str, KnowledgeState],
        gap_report: GapReport,
        version: int = 1,
        generation_reason: str = "Initial personalized roadmap generated from assessment"
    ) -> Roadmap:
        graph = self.graph_service.get_graph(goal_id)
        if not graph:
            return Roadmap(
                roadmap_id=f"rdm_{uuid.uuid4().hex[:8]}",
                learner_id=profile.learner_id,
                goal_id=goal_id,
                version=version,
                generation_reason="Error: Skill graph not found"
            )

        # Topological sorting ensures prerequisite dependencies come first
        ordered_skill_ids = self.graph_service.topological_sort(goal_id)
        
        stages: List[Stage] = []
        total_hours = 0.0
        rationale_list: List[str] = []

        # Filter skills that have gaps or need mastery/reinforcement
        relevant_skills = [
            sid for sid in ordered_skill_ids
            if sid in gap_report.weak_skills or sid in gap_report.needs_improvement_skills or sid in gap_report.unresolved_prerequisites
        ]

        if not relevant_skills:
            # If all are adequate, reinforce advanced skills
            relevant_skills = ordered_skill_ids[-3:]

        # Highlight early prerequisite bottlenecks
        if gap_report.unresolved_prerequisites:
            bottleneck_names = [
                graph.nodes[sid].name for sid in gap_report.unresolved_prerequisites
                if sid in graph.nodes
            ]
            rationale_list.append(
                f"Prioritizing prerequisite foundations ({', '.join(bottleneck_names)}) to unlock advanced downstream modules."
            )

        stage_idx = 1
        for sid in relevant_skills:
            node = graph.nodes.get(sid)
            if not node:
                continue

            ks = knowledge_states.get(sid)
            demonstrated = ks.demonstrated_score if ks else 0.0
            gap = gap_report.skill_gaps.get(sid, 0.5)

            # Estimate hours based on gap magnitude
            base_hours = 8.0 if node.difficulty == "beginner" else (14.0 if node.difficulty == "intermediate" else 20.0)
            stage_hours = round(base_hours * max(0.5, gap), 1)
            total_hours += stage_hours

            # Retrieve recommendations for this skill
            recs = self.recommender.recommend_for_skill(sid, knowledge_states, profile, max_results=2)

            # Build milestone
            milestone = Milestone(
                milestone_id=f"ms_{stage_idx:02d}_{sid}",
                title=f"Milestone {stage_idx}: Master {node.name}",
                description=f"Demonstrate applied competency in {node.name} concepts and complete hands-on deliverables.",
                success_criteria=[
                    f"Complete recommended core materials for {node.name}",
                    f"Achieve >= {int(node.target_proficiency * 100)}% on checkpoint assessment",
                    f"Build and submit project deliverable for {node.name}"
                ],
                assessment_ids=node.assessment_item_ids,
                project_ids=[r.resource_id for r in recs if r.resource_type == "project"],
                completed=False
            )

            # Build rationale
            if sid in gap_report.unresolved_prerequisites:
                stage_rationale = f"Critical prerequisite bottleneck: Demonstrated score is {int(demonstrated * 100)}% vs target {int(node.target_proficiency * 100)}%. Must resolve before advanced modules."
            else:
                stage_rationale = f"Core competency module: Required for {graph.target_role} profile."

            stage = Stage(
                stage_id=f"stage_{stage_idx:02d}_{sid}",
                title=f"Stage {stage_idx}: {node.name}",
                objective=f"Build practical proficiency in {node.description}",
                prerequisite_stage_ids=[f"stage_{stage_idx-1:02d}"] if stage_idx > 1 else [],
                estimated_hours=stage_hours,
                milestone=milestone,
                skill_targets=[sid],
                resources=recs,
                completion_status="in_progress" if stage_idx == 1 else "not_started",
                rationale=stage_rationale
            )
            stages.append(stage)
            stage_idx += 1

        rationale_list.append(
            f"Roadmap spans {len(stages)} ordered stages totaling ~{int(total_hours)} hours (approx. {round(total_hours / profile.weekly_hours, 1)} weeks at {profile.weekly_hours}h/week)."
        )

        return Roadmap(
            roadmap_id=f"rdm_{uuid.uuid4().hex[:8]}",
            learner_id=profile.learner_id,
            goal_id=goal_id,
            version=version,
            generated_at=datetime.utcnow().isoformat(),
            generation_reason=generation_reason,
            total_estimated_hours=total_hours,
            stages=stages,
            rationale=rationale_list
        )
