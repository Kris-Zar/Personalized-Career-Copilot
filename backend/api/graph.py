from fastapi import APIRouter, Depends, HTTPException
from core.schemas.skill_graph import SkillGraph
from core.services.graph_service import GraphService
from backend.dependencies import get_graph_service

router = APIRouter(prefix="/skill-graph", tags=["Skill Graph"])

@router.get("/{goal_id}", response_model=SkillGraph)
def get_skill_graph(
    goal_id: str,
    graph_service: GraphService = Depends(get_graph_service)
) -> SkillGraph:
    """Retrieve the competency DAG for a given career goal track."""
    graph = graph_service.get_graph(goal_id)
    if not graph:
        # Fallback to default graph if goal_id not directly matched
        graph = graph_service.get_graph("goal_data_scientist")
    if not graph:
        raise HTTPException(status_code=404, detail=f"Skill graph for '{goal_id}' not found.")
    return graph
