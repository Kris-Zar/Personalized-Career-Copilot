from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException
from core.schemas.profile import LearnerProfile
from core.schemas.feedback import GoalState
from core.storage.store import InMemoryStore
from core.services.graph_service import GraphService
from core.services.assessment_service import AssessmentService
from core.services.knowledge_service import KnowledgeStateEngine
from core.services.gap_analyzer import GapAnalyzer
from core.services.roadmap_engine import RoadmapEngine
from backend.dependencies import (
    get_store, get_graph_service, get_assessment_service,
    get_knowledge_engine, get_gap_analyzer, get_roadmap_engine
)

router = APIRouter(prefix="/presets", tags=["Demo Presets"])

PRESET_DEFINITIONS = {
    "alex": {
        "name": "Alex Chen",
        "role": "Biology Student",
        "goal_id": "goal_data_scientist",
        "target_role": "Data Scientist",
        "hours": 8.0,
        "timeline": 6,
        "interests": ["Machine Learning", "Computational Biology"],
        "self_reported": {
            "py_core": 0.85,
            "py_data": 0.75,
            "math_prob_stats": 0.80, # Claimed high
            "ml_foundations": 0.50
        }
    },
    "kenji": {
        "name": "Kenji Tanaka",
        "role": "ML Research Scientist (Academia)",
        "goal_id": "goal_ml_engineer",
        "target_role": "Machine Learning Engineer",
        "hours": 5.0,
        "timeline": 5,
        "interests": ["PyTorch", "Distributed Systems", "MLOps"],
        "self_reported": {
            "py_core": 0.90,
            "math_linear_algebra": 0.95,
            "math_prob_stats": 0.90,
            "ml_foundations": 0.90,
            "ml_ops": 0.20 # Deficit
        }
    },
    "aisha": {
        "name": "Aisha Nwosu",
        "role": "High School Mathematics Teacher",
        "goal_id": "goal_data_scientist",
        "target_role": "Data Scientist",
        "hours": 3.0,
        "timeline": 12,
        "interests": ["Statistics", "Educational Data", "Python"],
        "self_reported": {
            "py_core": 0.20, # Deficit
            "math_prob_stats": 0.90,
            "math_linear_algebra": 0.85,
            "ml_foundations": 0.15
        }
    }
}

@router.get("", response_model=List[str])
def list_presets() -> List[str]:
    """List available demo personas."""
    return list(PRESET_DEFINITIONS.keys())

@router.post("/load/{preset_id}")
def load_preset(
    preset_id: str,
    store: InMemoryStore = Depends(get_store),
    graph_svc: GraphService = Depends(get_graph_service),
    assess_svc: AssessmentService = Depends(get_assessment_service),
    knowledge_eng: KnowledgeStateEngine = Depends(get_knowledge_engine),
    gap_analyzer: GapAnalyzer = Depends(get_gap_analyzer),
    roadmap_eng: RoadmapEngine = Depends(get_roadmap_engine)
) -> Dict[str, Any]:
    """Load a full persona into the store for testing."""
    key = preset_id.lower().strip()
    preset = PRESET_DEFINITIONS.get(key)
    if not preset:
        raise HTTPException(status_code=404, detail=f"Preset '{preset_id}' not found. Options: {list(PRESET_DEFINITIONS.keys())}")

    store.reset_to_fresh_state()
    store.profile = LearnerProfile(
        learner_id=f"learner_{key}",
        name=preset["name"],
        email=f"{key}@example.com",
        current_role=preset["role"],
        interests=preset["interests"],
        self_reported_skills=preset["self_reported"],
        previous_learning=["Intro Course", "Self-Study"],
        weekly_hours=preset["hours"],
        timeline_months=preset["timeline"],
        content_preferences=["projects", "interactive", "videos"]
    )

    store.goal_state = GoalState(
        goal_id=preset["goal_id"],
        target_role=preset["target_role"],
        timeline_months=preset["timeline"],
        weekly_hours=preset["hours"],
        target_proficiency_by_skill={k: 0.85 for k in preset["self_reported"].keys()},
        active=True
    )

    return {
        "status": "loaded",
        "preset": key,
        "profile": store.profile,
        "goal_state": store.goal_state
    }

@router.post("/reset")
def reset_store_state(store: InMemoryStore = Depends(get_store)) -> Dict[str, str]:
    """Reset store to clean blank slate."""
    store.reset_to_fresh_state()
    return {"status": "reset", "message": "Authoritative store reset to fresh state."}
