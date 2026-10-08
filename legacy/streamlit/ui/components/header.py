import streamlit as st
from typing import Optional
from core.storage.store import InMemoryStore

def render_header(store: Optional[InMemoryStore] = None):
    """
    Renders top navigation toolbar, theme toggle, and hero header
    matching PathFinder_Visual_Reference.html design specification.
    """
    theme = st.session_state.get("theme", "light")
    current_screen = st.session_state.get("current_screen", "profile")

    # Compute dynamic momentum XP & streak
    if store and store.assessment_attempts:
        attempt_xp = len(store.assessment_attempts) * 150
        feedback_xp = len(store.feedback_events) * 50
        current_xp = attempt_xp + feedback_xp
        streak_days = 1 if (store.assessment_attempts or store.feedback_events) else 0
        streak_label = f"{streak_days}-day streak"
        bar_width = min(100, max(5, int((current_xp / 1000) * 100)))
        momentum_text = f"{streak_label} · {current_xp}/1000 xp"
    elif store and (store.profile and store.profile.name):
        current_xp = 50
        bar_width = 5
        momentum_text = "1-day streak · 50/1000 xp"
    else:
        current_xp = 0
        bar_width = 0
        momentum_text = "0-day streak · 0/1000 xp"

    theme_label = "Velvet Purple Dark" if theme == "light" else "Medium Red Light"
    theme_icon = "🌙" if theme == "light" else "☀️"
    theme_badge_text = "☀️ Medium Red Light Active" if theme == "light" else "🌙 Velvet Purple Dark Active"

    screen_tabs = [
        ("profile", "01 · Profile"),
        ("chat", "02 · Goal Discovery"),
        ("assess", "03 · Assessment"),
        ("results", "04 · Results"),
        ("roadmap", "05 · Roadmap"),
        ("dash", "06 · Dashboard"),
    ]

    # Render Top Navigation Bar using Streamlit interactive columns
    t_col1, t_col2, t_col3 = st.columns([2.2, 5.5, 2.3])

    with t_col1:
        st.markdown(
            """
            <div style="display: flex; align-items: center; gap: 10px; height: 38px;">
                <div class="brand-dot"></div>
                <span style="font-family: 'Space Grotesk', sans-serif; font-weight: 800; font-size: 17px; color: var(--text-primary);">XCL PathFinder</span>
            </div>
            """,
            unsafe_allow_html=True
        )

    with t_col2:
        # Render 6 navigation buttons in a row styled like .nav-tabs
        nav_cols = st.columns(6)
        for idx, (s_key, s_label) in enumerate(screen_tabs):
            with nav_cols[idx]:
                is_active = (current_screen == s_key)
                btn_type = "primary" if is_active else "secondary"
                if st.button(s_label, key=f"top_nav_{s_key}", type=btn_type, use_container_width=True):
                    st.session_state["current_screen"] = s_key
                    st.rerun()

    with t_col3:
        if st.button(f"{theme_icon} {theme_label}", key="theme_toggle_btn", use_container_width=True):
            st.session_state["theme"] = "dark" if theme == "light" else "light"
            st.rerun()

    # Hero description & Theme badge
    st.markdown(
        f"""
        <div class="header-desc">
            <div>
                <h1>Welcome to <span>XCL PathFinder</span></h1>
                <p>Begin your personalized learning journey with evidence-based competency calibration.</p>
            </div>
            <div style="display: flex; align-items: center; gap: 12px;">
                <span class="theme-badge">{theme_badge_text}</span>
                <div class="momentum">
                    <span class="flame">🔥</span>
                    <div>
                        <div class="momentum-bar"><div class="momentum-fill" style="width: {bar_width}%;"></div></div>
                        <div class="momentum-label">{momentum_text}</div>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
