import streamlit as st
from core.storage.store import InMemoryStore

def render_profile_view(store: InMemoryStore):
    """
    Screen 01: Learner Profile & Self-Reported Baseline
    Visual fidelity with PathFinder_Visual_Reference.html
    """
    profile = store.profile

    st.markdown(
        """
        <div class="screen-frame">
            <div class="screen-tag">
                <span>01 · Learner Profile &amp; Self-Reported Baseline</span>
                <span class="screen-pill">Step 1 of 6</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    with st.container():
        st.markdown('<div class="profile-wrap">', unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input(
                "Full Name",
                value=profile.name if profile.name else "",
                placeholder="e.g. Alex Chen",
                key="prof_name"
            )
            role = st.text_input(
                "Current Background / Role",
                value=profile.current_role if profile.current_role else "",
                placeholder="e.g. Biology Student / Software Developer",
                key="prof_role"
            )
            hours = st.number_input(
                "Weekly Study Time (Hours / Week)",
                min_value=1.0,
                max_value=40.0,
                value=float(profile.weekly_hours if profile.weekly_hours else 8.0),
                step=1.0,
                key="prof_hours"
            )

        with col2:
            timeline = st.number_input(
                "Target Timeline (Months)",
                min_value=1,
                max_value=24,
                value=int(profile.timeline_months if profile.timeline_months else 6),
                step=1,
                key="prof_timeline"
            )
            interests_str = st.text_input(
                "Primary Interests (comma-separated)",
                value=", ".join(profile.interests) if profile.interests else "Machine Learning, Applied AI",
                placeholder="e.g. Data Science, Machine Learning",
                key="prof_interests"
            )
            prefs = st.multiselect(
                "Preferred Content Formats",
                options=["projects", "interactive", "videos", "articles", "books"],
                default=profile.content_preferences if profile.content_preferences else ["projects", "interactive", "videos"],
                key="prof_prefs"
            )

        st.markdown(
            """
            <div style="margin-top: 14px; margin-bottom: 6px;">
                <label class="form-label">Self-Reported Skill Baseline (Signal 5)</label>
                <p style="font-size: 12px; color: var(--text-secondary); margin: 0 0 10px 0;">
                    Estimate your confidence level across core competencies (0.0 to 1.0). Diagnostic tests will calibrate this baseline.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

        skill_cols = st.columns(3)
        skill_labels = {
            "py_core": "Python Core & OOP",
            "py_data": "Pandas & Data Processing",
            "math_prob_stats": "Probability & Statistics",
            "math_linear_algebra": "Linear Algebra",
            "math_calculus": "Calculus & Gradients",
            "ml_foundations": "Classical Machine Learning",
            "dl_neural_nets": "Deep Learning / PyTorch",
            "nlp_transformers": "NLP & LLMs",
            "cv_vision": "Computer Vision"
        }

        updated_self_skills = {}
        for idx, (sid, label) in enumerate(skill_labels.items()):
            col = skill_cols[idx % 3]
            with col:
                val = profile.self_reported_skills.get(sid, 0.5)
                new_val = st.slider(f"{label}", 0.0, 1.0, float(val), 0.05, key=f"self_rep_{sid}")
                updated_self_skills[sid] = new_val

        st.markdown('<div style="text-align: right; margin-top: 20px;">', unsafe_allow_html=True)
        if st.button("Continue to Goal Discovery ➔", type="primary", use_container_width=False, key="prof_submit"):
            profile.name = name.strip() if name.strip() else "Learner"
            profile.current_role = role.strip() if role.strip() else "Learner"
            profile.weekly_hours = float(hours)
            profile.timeline_months = int(timeline)
            profile.interests = [i.strip() for i in interests_str.split(",") if i.strip()]
            profile.content_preferences = prefs
            profile.self_reported_skills = updated_self_skills

            st.session_state["current_screen"] = "chat"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)
