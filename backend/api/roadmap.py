from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from core.schemas.roadmap import Roadmap
from core.storage.store import InMemoryStore
from core.services.roadmap_engine import RoadmapEngine
from core.services.adaptation_engine import AdaptationEngine
from backend.dependencies import get_store, get_roadmap_engine, get_adaptation_engine
from backend.schemas import RoadmapGenerateRequest, FeedbackSubmitRequest

router = APIRouter(prefix="/roadmap", tags=["Roadmap"])

@router.get("", response_model=Optional[Roadmap])
def get_current_roadmap(
    version: Optional[int] = Query(None, description="Optional specific version number"),
    store: InMemoryStore = Depends(get_store)
) -> Optional[Roadmap]:
    """Retrieve active or specified version of the personalized learning roadmap."""
    if version:
        return store.get_roadmap_by_version(version)
    return store.get_current_roadmap()

@router.get("/versions", response_model=Dict[int, Roadmap])
def get_roadmap_versions(store: InMemoryStore = Depends(get_store)) -> Dict[int, Roadmap]:
    """Retrieve all historical and active versions of the roadmap."""
    return store.roadmaps

@router.post("/generate", response_model=Roadmap)
def generate_roadmap(
    req: RoadmapGenerateRequest,
    store: InMemoryStore = Depends(get_store),
    roadmap_eng: RoadmapEngine = Depends(get_roadmap_engine)
) -> Roadmap:
    """Generate or re-sequence personalized roadmap from current knowledge state and gap report."""
    goal_id = req.goal_id or (store.goal_state.goal_id if store.goal_state else "goal_data_scientist")
    if not store.knowledge_states:
        raise HTTPException(status_code=400, detail="Cannot generate roadmap: Knowledge assessment not completed.")

    new_version = len(store.roadmaps) + 1
    roadmap = roadmap_eng.generate_roadmap(
        goal_id=goal_id,
        profile=store.profile,
        knowledge_states=store.knowledge_states,
        gap_report=store.gap_report,
        version=new_version,
        generation_reason=req.generation_reason
    )
    store.save_roadmap(roadmap)
    return roadmap
