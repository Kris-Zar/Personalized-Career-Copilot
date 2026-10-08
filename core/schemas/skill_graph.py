from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class SkillNode(BaseModel):
    skill_id: str
    name: str
    description: str
    category: str = "General"
    parent_skill_id: Optional[str] = None
    prerequisite_skill_ids: List[str] = Field(default_factory=list)
    target_proficiency: float = Field(default=0.8, ge=0.0, le=1.0)
    assessment_item_ids: List[str] = Field(default_factory=list)
    recommended_resource_types: List[str] = Field(default_factory=lambda: ["course", "project"])
    difficulty: str = "intermediate"  # beginner, intermediate, advanced
    tags: List[str] = Field(default_factory=list)

class SkillGraph(BaseModel):
    goal_id: str
    title: str
    description: str
    target_role: str
    nodes: Dict[str, SkillNode]
