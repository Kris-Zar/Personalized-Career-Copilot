from fastapi import APIRouter, Depends
from core.storage.store import InMemoryStore
from backend.dependencies import get_store
from backend.schemas import DashboardResponse

router = APIRouter(prefix="/dashboard", tags=["Dashboard Cockpit"])

@router.get("", response_model=DashboardResponse)
def get_dashboard_data(store: InMemoryStore = Depends(get_store)) -> DashboardResponse:
    """
    Retrieve unified cockpit metrics, baseline competency evidence, active roadmap,
    and chat history from the authoritative store.
    """
    learner_name = store.profile.name if (store.profile and store.profile.name) else "Learner"
    target_role = store.goal_state.target_role if store.goal_state else "Data Scientist"
    timeline_months = store.goal_state.timeline_months if store.goal_state else 6
    weekly_hours = store.goal_state.weekly_hours if store.goal_state else 8.0

    current_roadmap = store.get_current_roadmap()
    if current_roadmap and current_roadmap.stages:
        completed_stages = sum(
            1 for s in current_roadmap.stages
            if s.completion_status == "completed" or (s.milestone and s.milestone.completed)
        )
        progress_pct = int((completed_stages / len(current_roadmap.stages)) * 100)
    else:
        progress_pct = 0

    skills_assessed_count = len(set(att.skill_id for att in store.assessment_attempts)) if store.assessment_attempts else 0
    weak_prereq_count = len(store.gap_report.unresolved_prerequisites) if store.gap_report else 0

    return DashboardResponse(
        learner_name=learner_name,
        target_role=target_role,
        timeline_months=timeline_months,
        weekly_hours=weekly_hours,
        progress_percentage=progress_pct,
        skills_assessed_count=skills_assessed_count,
        weak_prerequisites_count=weak_prereq_count,
        streak_days=3,
        current_xp=1250,
        knowledge_states=list(store.knowledge_states.values()),
        gap_report=store.gap_report,
        current_roadmap=current_roadmap,
        chat_history=store.chat_history
    )
