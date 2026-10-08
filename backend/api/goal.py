import json
import os
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from core.schemas.feedback import GoalState
from core.storage.store import InMemoryStore
from core.services.llm_service import LLMService, LLMResult
from backend.dependencies import get_store, get_llm_service
from backend.schemas import GoalExtractRequest, GoalExtractResponse, GoalSelectRequest

router = APIRouter(prefix="/goal", tags=["Goal Discovery"])

def _load_goals_catalog() -> List[Dict[str, Any]]:
    path = "data/goals/goals.json"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

@router.get("", response_model=Optional[GoalState])
def get_current_goal(store: InMemoryStore = Depends(get_store)) -> Optional[GoalState]:
    """Retrieve active career goal state from authoritative store."""
    return store.goal_state

@router.get("/catalog", response_model=List[Dict[str, Any]])
def get_goals_catalog() -> List[Dict[str, Any]]:
    """Retrieve all available career tracks from the goals catalog."""
    return _load_goals_catalog()

@router.post("/extract", response_model=GoalExtractResponse)
def extract_goal_and_activate(
    req: GoalExtractRequest,
    store: InMemoryStore = Depends(get_store),
    llm: LLMService = Depends(get_llm_service)
) -> GoalExtractResponse:
    """
    Extract structured goal parameters via Gemini 3.6 Flash and activate matching catalog track.
    """
    llm_result: LLMResult = llm.extract_goal_and_constraints(req.user_prompt)
    extracted = llm_result.value

    target_str = str(extracted.get("target_role", "Data Scientist")).lower()
    timeline_months = int(extracted.get("timeline_months", 6))
    weekly_hours = float(extracted.get("weekly_hours", 8.0))

    catalog = _load_goals_catalog()
    matched_goal = None
    for g in catalog:
        if g["target_role"].lower() in target_str or target_str in g["target_role"].lower():
            matched_goal = g
            break
    if not matched_goal and catalog:
        matched_goal = catalog[0]

    if matched_goal:
        store.goal_state = GoalState(
            goal_id=matched_goal["goal_id"],
            target_role=matched_goal["target_role"],
            timeline_months=timeline_months or matched_goal["recommended_timeline_months"],
            weekly_hours=weekly_hours or matched_goal["recommended_weekly_hours"],
            target_proficiency_by_skill=matched_goal["target_proficiency_by_skill"],
            active=True
        )
    else:
        store.goal_state = GoalState(
            goal_id="goal_custom",
            target_role=extracted.get("target_role", "Data Scientist"),
            timeline_months=timeline_months,
            weekly_hours=weekly_hours,
            target_proficiency_by_skill={"py_core": 0.85, "math_prob_stats": 0.85, "ml_foundations": 0.85},
            active=True
        )

    return GoalExtractResponse(
        extracted=extracted,
        goal_state=store.goal_state,
        source=llm_result.source,
        model=llm.model_name,
        error=llm_result.error
    )

@router.post("/select", response_model=GoalState)
def select_goal_track(
    req: GoalSelectRequest,
    store: InMemoryStore = Depends(get_store)
) -> GoalState:
    """Manually select and activate a career goal from the catalog."""
    catalog = _load_goals_catalog()
    matched_goal = next((g for g in catalog if g["goal_id"] == req.goal_id), None)
    if not matched_goal:
        raise HTTPException(status_code=404, detail=f"Goal with id '{req.goal_id}' not found.")

    store.goal_state = GoalState(
        goal_id=matched_goal["goal_id"],
        target_role=req.target_role or matched_goal["target_role"],
        timeline_months=req.timeline_months or matched_goal["recommended_timeline_months"],
        weekly_hours=req.weekly_hours or matched_goal["recommended_weekly_hours"],
        target_proficiency_by_skill=matched_goal["target_proficiency_by_skill"],
        active=True
    )
    return store.goal_state
