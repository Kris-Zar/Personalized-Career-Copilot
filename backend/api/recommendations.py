from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from core.schemas.resource import Recommendation, Resource
from core.storage.store import InMemoryStore
from core.services.recommender import RecommendationEngine
from backend.dependencies import get_store, get_recommender

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])

@router.get("", response_model=List[Recommendation])
def get_recommendations(
    skill_id: Optional[str] = Query(None, description="Optional skill_id filter"),
    store: InMemoryStore = Depends(get_store),
    recommender: RecommendationEngine = Depends(get_recommender)
) -> List[Recommendation]:
    """Retrieve multi-signal ranked learning resources tailored to learner profile."""
    profile = store.profile
    if skill_id:
        return recommender.get_resources_for_skill(skill_id=skill_id, profile=profile)
    
    # Otherwise return curated resources across all weak/deficit skills
    weak_skills = store.gap_report.weak_skills if store.gap_report else []
    all_res = []
    for s_id in weak_skills[:3]:
        all_res.extend(recommender.get_resources_for_skill(skill_id=s_id, profile=profile))
    return all_res or recommender.get_all_resources()[:8]
