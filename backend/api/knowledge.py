from typing import List
from fastapi import APIRouter, Depends
from core.schemas.assessment import KnowledgeState
from core.storage.store import InMemoryStore
from backend.dependencies import get_store

router = APIRouter(prefix="/knowledge", tags=["Knowledge State"])

@router.get("", response_model=List[KnowledgeState])
def get_knowledge_states(store: InMemoryStore = Depends(get_store)) -> List[KnowledgeState]:
    """Retrieve calibrated evidence-based knowledge states for all skills."""
    return list(store.knowledge_states.values())
