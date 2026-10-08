import uuid
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from core.schemas.assessment import AssessmentItem, AssessmentAttempt, KnowledgeState, GapReport
from core.schemas.roadmap import Roadmap
from core.storage.store import InMemoryStore
from core.services.assessment_service import AssessmentService
from core.services.knowledge_service import KnowledgeStateEngine
from core.services.gap_analyzer import GapAnalyzer
from core.services.roadmap_engine import RoadmapEngine
from core.services.graph_service import GraphService
from backend.dependencies import (
    get_store, get_assessment_service, get_knowledge_engine,
    get_gap_analyzer, get_roadmap_engine, get_graph_service
)
from backend.schemas import AttemptSubmitRequest, AssessmentCompleteRequest

router = APIRouter(prefix="/assessment", tags=["Assessment"])

@router.get("", response_model=List[AssessmentItem])
def get_assessment_items(
    assess_svc: AssessmentService = Depends(get_assessment_service)
) -> List[AssessmentItem]:
    """Retrieve all diagnostic assessment items across core competencies."""
    return assess_svc.get_all_items()

@router.post("/attempt", response_model=AssessmentAttempt)
def record_attempt(
    req: AttemptSubmitRequest,
    store: InMemoryStore = Depends(get_store),
    assess_svc: AssessmentService = Depends(get_assessment_service)
) -> AssessmentAttempt:
    """Record an individual diagnostic item answer attempt."""
    item = assess_svc.get_item(req.item_id)
    if not item:
        raise HTTPException(status_code=404, detail=f"Assessment item '{req.item_id}' not found.")

    is_correct = (req.answer.strip() == item.correct_answer.strip())
    attempt = AssessmentAttempt(
        attempt_id=f"att_{uuid.uuid4().hex[:6]}",
        learner_id=store.profile.learner_id if store.profile else "learner_001",
        goal_id=store.goal_state.goal_id if store.goal_state else "goal_data_scientist",
        item_id=req.item_id,
        skill_id=item.skill_id,
        answer=req.answer,
        correct=is_correct
    )
    store.add_attempt(attempt)
    return attempt

@router.post("/complete")
def complete_assessment_and_calibrate(
    req: AssessmentCompleteRequest,
    store: InMemoryStore = Depends(get_store),
    assess_svc: AssessmentService = Depends(get_assessment_service),
    knowledge_eng: KnowledgeStateEngine = Depends(get_knowledge_engine),
    gap_analyzer: GapAnalyzer = Depends(get_gap_analyzer),
    roadmap_eng: RoadmapEngine = Depends(get_roadmap_engine),
    graph_svc: GraphService = Depends(get_graph_service)
) -> Dict[str, Any]:
    """
    Score all attempts, compute evidence-based KnowledgeState, run Gap Analysis,
    and generate Roadmap V1.
    """
    # If explicit attempts submitted in body, record them
    if req.attempts:
        attempts_list = []
        for att_req in req.attempts:
            item = assess_svc.get_item(att_req.item_id)
            if not item:
                continue
            is_correct = (att_req.answer.strip() == item.correct_answer.strip())
            attempts_list.append(
                AssessmentAttempt(
                    attempt_id=f"att_{uuid.uuid4().hex[:6]}",
                    learner_id=store.profile.learner_id if store.profile else "learner_001",
                    goal_id=store.goal_state.goal_id if store.goal_state else "goal_data_scientist",
                    item_id=item.item_id,
                    skill_id=item.skill_id,
                    answer=att_req.answer,
                    correct=is_correct
                )
            )
        store.assessment_attempts = attempts_list

    if not store.assessment_attempts:
        raise HTTPException(status_code=400, detail="No assessment attempts to score.")

    goal_id = store.goal_state.goal_id if store.goal_state else "goal_data_scientist"
    graph = graph_svc.get_graph(goal_id) or graph_svc.get_graph("goal_data_scientist")

    # 1. Compute Knowledge States from evidence
    k_states = knowledge_eng.compute_knowledge_states(
        skill_graph=graph,
        attempts=store.assessment_attempts,
        self_reported_skills=store.profile.self_reported_skills if store.profile else {}
    )
    store.knowledge_states = k_states

    # 2. Compute Gap Report
    gap_rep = gap_analyzer.analyze_gaps(
        goal_id=goal_id,
        knowledge_states=k_states,
        self_reported_skills=store.profile.self_reported_skills if store.profile else {}
    )
    store.gap_report = gap_rep

    # 3. Generate Roadmap V1
    roadmap = roadmap_eng.generate_roadmap(
        goal_id=goal_id,
        profile=store.profile,
        knowledge_states=k_states,
        gap_report=gap_rep,
        version=1,
        generation_reason="Initial personalized roadmap generated from diagnostic assessment"
    )
    store.save_roadmap(roadmap)

    return {
        "status": "success",
        "scored_attempts_count": len(store.assessment_attempts),
        "knowledge_states": list(k_states.values()),
        "gap_report": gap_rep,
        "roadmap_v1": roadmap
    }
