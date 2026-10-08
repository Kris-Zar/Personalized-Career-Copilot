import uuid
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException
from core.schemas.feedback import FeedbackEvent
from core.schemas.roadmap import Roadmap
from core.storage.store import InMemoryStore
from core.services.adaptation_engine import AdaptationEngine
from backend.dependencies import get_store, get_adaptation_engine
from backend.schemas import FeedbackSubmitRequest

router = APIRouter(prefix="/feedback", tags=["Feedback & Adaptation"])

@router.get("", response_model=List[FeedbackEvent])
def get_feedback_history(store: InMemoryStore = Depends(get_store)) -> List[FeedbackEvent]:
    """Retrieve all logged learner feedback events."""
    return store.feedback_events

@router.post("", response_model=Roadmap)
def submit_feedback_and_adapt(
    req: FeedbackSubmitRequest,
    store: InMemoryStore = Depends(get_store),
    adaptation_engine: AdaptationEngine = Depends(get_adaptation_engine)
) -> Roadmap:
    """
    Log explicit learner feedback and trigger continuous roadmap adaptation.
    """
    current_roadmap = store.get_current_roadmap()
    if not current_roadmap:
        raise HTTPException(status_code=400, detail="Cannot adapt: No active roadmap found.")

    fb_event = FeedbackEvent(
        feedback_id=f"fb_{uuid.uuid4().hex[:6]}",
        learner_id=store.profile.learner_id if store.profile else "learner_001",
        source=req.source or "manual",
        type=req.type or "difficulty",
        target_id=req.target_id or "math_prob_stats",
        message=req.message,
        extracted_signal={"chat_feedback": req.message}
    )
    store.record_feedback(fb_event)

    new_roadmap, diff_summary = adaptation_engine.process_feedback(
        event=fb_event,
        profile=store.profile,
        knowledge_states=store.knowledge_states,
        current_roadmap=current_roadmap
    )
    store.save_roadmap(new_roadmap)
    return new_roadmap
