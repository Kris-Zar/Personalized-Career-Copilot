import streamlit as st
from typing import Dict, Any, List, Optional
from core.schemas.feedback import FeedbackEvent
from core.services.llm_service import LLMService
from core.services.adaptation_engine import AdaptationEngine
from core.storage.store import InMemoryStore

def render_chat_assistant(
    store: InMemoryStore,
    llm_service: LLMService,
    adaptation_engine: AdaptationEngine
):
    """
    Renders conversational tutor with visual reference card design.
    """
    st.markdown(
        """
        <div style="margin-bottom: 12px;">
            <h3 style="margin: 0 0 2px 0;">💬 AI Copilot &amp; Tutor</h3>
            <div style="font-size: 12px; color: var(--text-secondary);">Ask questions, clarify concepts, or log difficulty to trigger roadmap adaptation.</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Quick Prompts
    st.markdown("<div style='font-size: 12px; font-weight: 700; color: var(--c-coral); margin-bottom: 6px;'>⚡ Quick Prompts:</div>", unsafe_allow_html=True)
    
    if st.button("❓ Why recommend Probability before ML?", key="qp_1", use_container_width=True):
        st.session_state["pending_chat_prompt"] = "Why did you recommend Probability and Statistics before Machine Learning?"

    if st.button("⚡ 'Probability is too difficult (30m/day)'", key="qp_2", use_container_width=True):
        st.session_state["pending_chat_prompt"] = "Probability is too difficult and I only have 30 minutes today."

    if st.button("📖 Explain Bayes' Theorem for ML", key="qp_3", use_container_width=True):
        st.session_state["pending_chat_prompt"] = "Can you explain Bayes' Theorem in the context of machine learning?"

    # Display Chat History
    chat_container = st.container(height=360)
    with chat_container:
        for message in store.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # Chat Input Handling
    user_input = st.chat_input("Ask why probability blocks the next stage...")
    if "pending_chat_prompt" in st.session_state and st.session_state["pending_chat_prompt"]:
        user_input = st.session_state.pop("pending_chat_prompt")

    if user_input:
        store.chat_history.append({"role": "user", "content": user_input})

        current_roadmap = store.get_current_roadmap()
        lower_input = user_input.lower()
        is_feedback = any(k in lower_input for k in ["difficult", "hard", "confusing", "less time", "30 min", "project", "too fast", "too slow"])

        if is_feedback and current_roadmap:
            fb_type = "time_constraint" if "time" in lower_input or "30 min" in lower_input else "difficulty"
            fb_event = FeedbackEvent(
                feedback_id=f"fb_{len(store.feedback_events)+1:03d}",
                learner_id=store.profile.learner_id,
                source="chat",
                type=fb_type,
                target_id="math_prob_stats",
                message=user_input,
                extracted_signal={"chat_feedback": user_input}
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
                f"Understood, {store.profile.name}! I have recorded your feedback and updated your learner model.\n\n"
                f"🔄 **Roadmap Adapted to Version {new_roadmap.version}:**\n"
                f"{diff_summary}\n\n"
                f"I've injected bite-sized interactive visual exercises into **Stage 1 (Probability & Statistics)** to build intuition smoothly. Check out your updated roadmap!"
            )
        else:
            assistant_reply = llm_service.answer_tutoring_query(
                query=user_input,
                profile=store.profile,
                current_roadmap=current_roadmap,
                knowledge_states=store.knowledge_states,
                gap_report=store.gap_report,
                skill_graph=None
            )

        store.chat_history.append({"role": "assistant", "content": assistant_reply})
        st.rerun()
