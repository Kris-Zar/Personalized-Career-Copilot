from fastapi import APIRouter, Depends, HTTPException
from core.schemas.profile import LearnerProfile
from core.storage.store import InMemoryStore
from backend.dependencies import get_store
from backend.schemas import ProfileUpdateRequest

router = APIRouter(prefix="/profile", tags=["Profile"])

@router.get("", response_model=LearnerProfile)
def get_profile(store: InMemoryStore = Depends(get_store)) -> LearnerProfile:
    """Retrieve the current learner profile baseline from authoritative store."""
    if not store.profile:
        store.reset_to_fresh_state()
    return store.profile

@router.put("", response_model=LearnerProfile)
def update_profile(
    req: ProfileUpdateRequest,
    store: InMemoryStore = Depends(get_store)
) -> LearnerProfile:
    """Update learner profile baseline and persist in authoritative store."""
    if not store.profile:
        store.reset_to_fresh_state()

    store.profile.name = req.name.strip()
    store.profile.email = req.email.strip() if req.email else ""
    store.profile.current_role = req.current_role.strip()
    store.profile.interests = req.interests
    store.profile.self_reported_skills = req.self_reported_skills
    store.profile.previous_learning = req.previous_learning
    store.profile.weekly_hours = req.weekly_hours
    store.profile.timeline_months = req.timeline_months
    store.profile.content_preferences = req.content_preferences

    return store.profile
