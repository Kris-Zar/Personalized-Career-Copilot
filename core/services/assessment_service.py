import json
import os
from typing import Dict, List, Optional
from core.schemas.assessment import AssessmentItem, AssessmentAttempt

class AssessmentService:
    """
    Delivers diagnostic items, scores user attempts,
    and applies difficulty & evidence weights.
    """
    def __init__(self, data_path: str = "data/assessment/assessment_bank.json"):
        self.data_path = data_path
        self.items: Dict[str, AssessmentItem] = {}
        self._load_items()

    def _load_items(self):
        if not os.path.exists(self.data_path):
            return
        try:
            with open(self.data_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item_dict in data:
                    item = AssessmentItem(**item_dict)
                    self.items[item.item_id] = item
        except Exception as e:
            print(f"Error loading assessment bank: {e}")

    def get_items_for_skills(self, skill_ids: List[str]) -> List[AssessmentItem]:
        """Return all assessment items corresponding to a list of skill IDs."""
        return [item for item in self.items.values() if item.skill_id in skill_ids]

    def get_all_items(self) -> List[AssessmentItem]:
        return list(self.items.values())

    def get_item(self, item_id: str) -> Optional[AssessmentItem]:
        return self.items.get(item_id)

    def score_attempt(self, attempt: AssessmentAttempt) -> bool:
        """Evaluate attempt correctness against answer bank."""
        item = self.get_item(attempt.item_id)
        if not item:
            return False
        is_correct = (attempt.answer.strip() == item.correct_answer.strip())
        attempt.correct = is_correct
        return is_correct
