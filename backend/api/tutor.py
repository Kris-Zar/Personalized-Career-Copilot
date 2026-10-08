import uuid
from typing import Dict, Any
from fastapi import APIRouter, Depends
from core.schemas.feedback import FeedbackEvent
from core.storage.store import InMemoryStore
from core.services.llm_service import LLMService, LLMResult
from core.services.adaptation_engine import AdaptationEngine
from backend.dependencies import get_store, get_llm_service, get_adaptation_engine
from backend.schemas import TutorChatRequest, TutorChatResponse

router = APIRouter(prefix="/tutor", tags=["AI Tutor"])

@router.post("/chat", response_model=TutorChatResponse)
def handle_tutor_query(
    req: TutorChatRequest,
    store: InMemoryStore = Depends(get_store),
    llm: LLMService = Depends(get_llm_service),
    adaptation_engine: AdaptationEngine = Depends(get_adaptation_engine)
) -> TutorChatResponse:
    """
    Process learner tutoring query with grounded Gemini AI.
    Detects learning difficulty / feedback signals and triggers dynamic continuous adaptation.
    """
    user_query = req.query.strip()
    store.chat_history.append({"role": "user", "content": user_query})

    current_roadmap = store.get_current_roadmap()
    lower_input = user_query.lower()
    is_feedback = any(k in lower_input for k in [
        "difficult", "hard", "confusing", "less time", "30 min", "project",
        "too fast", "too slow", "overwhelmed", "daily", "cannot study", "skip"
    ])

    if is_feedback and current_roadmap:
        fb_type = "time_constraint" if any(t in lower_input for t in ["time", "30 min", "daily", "hour"]) else "difficulty"
        target_skill = store.gap_report.weak_skills[0] if (store.gap_report and store.gap_report.weak_skills) else "math_prob_stats"

        fb_event = FeedbackEvent(
            feedback_id=f"fb_{uuid.uuid4().hex[:6]}",
            learner_id=store.profile.learner_id if store.profile else "learner_001",
            source="chat",
            type=fb_type,
            target_id=target_skill,
            message=user_query,
            extracted_signal={"chat_feedback": user_query}
        )
        store.record_feedback(fb_event)

        new_roadmap, diff_summary = adaptation_engine.process_feedback(
            event=fb_event,
            profile=store.profile,
            knowledge_states=store.knowledge_states,
            current_roadmap=current_roadmap
        )
        store.save_roadmap(new_roadmap)

        assistant_reply = (
            f"Understood, {store.profile.name if store.profile else 'Learner'}! I have recorded your feedback and updated your learner model.\n\n"
            f"🔄 **Roadmap Adapted to Version {new_roadmap.version}:**\n"
            f"{diff_summary}\n\n"
            f"I've injected bite-sized interactive exercises and adjusted pacing. Check out your updated Roadmap!"
        )

        store.chat_history.append({"role": "assistant", "content": assistant_reply})
        return TutorChatResponse(
            reply=assistant_reply,
            source="adaptation_engine",
            model="adaptation-engine-v2",
            is_adaptation=True,
            adaptation_diff=new_roadmap.adaptation_diff
        )

    # Standard Pedagogical Query -> Gemini 3.6 Flash
    llm_result: LLMResult = llm.answer_tutoring_query(
        query=user_query,
        profile=store.profile,
        current_roadmap=current_roadmap,
        knowledge_states=store.knowledge_states,
        gap_report=store.gap_report,
        skill_graph=None
    )

    assistant_reply = llm_result.value
    store.chat_history.append({"role": "assistant", "content": assistant_reply})

    return TutorChatResponse(
        reply=assistant_reply,
        source=llm_result.source,
        model=llm.model_name,
        is_adaptation=False
    )
