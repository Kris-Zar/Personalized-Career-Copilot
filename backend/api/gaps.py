from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from core.schemas.assessment import GapReport
from core.storage.store import InMemoryStore
from backend.dependencies import get_store

router = APIRouter(prefix="/gaps", tags=["Gap Analysis"])

@router.get("", response_model=Optional[GapReport])
def get_gap_report(store: InMemoryStore = Depends(get_store)) -> Optional[GapReport]:
    """Retrieve the computed skill gap analysis report."""
    return store.gap_report
