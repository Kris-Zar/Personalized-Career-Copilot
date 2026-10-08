import streamlit as st
from typing import Dict, Optional
from core.schemas.roadmap import Roadmap

def render_roadmap_view(
    roadmaps: Dict[int, Roadmap],
    current_version: int,
    on_version_change=None,
    on_milestone_toggle=None
):
    """
    Renders versioned adaptive roadmap with dynamic connected horizontal stage track,
    milestones, and curated resources.
    """
    roadmap = roadmaps.get(current_version)
    if not roadmap or not roadmap.stages:
        st.info("No roadmap generated yet. Complete the assessment or click 'Generate Roadmap' to begin.")
        return

    # Header with Version Switcher
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader(f"🗺️ Personalized Learning Roadmap (Version {roadmap.version})")
        st.caption(f"Generated: {roadmap.generated_at[:10]} • Total Estimated Effort: ~{int(roadmap.total_estimated_hours)} hours")
    with col2:
        available_versions = sorted(list(roadmaps.keys()))
        selected_version = st.selectbox(
            "Version History",
            options=available_versions,
            index=available_versions.index(current_version),
            format_func=lambda v: f"Roadmap v{v}" + (" (Current)" if v == current_version else "")
        )

    # Show Adaptation Diff if available
    if roadmap.adaptation_diff:
        diff = roadmap.adaptation_diff
        st.markdown(
            f"""
            <div style="background: rgba(239, 99, 81, 0.14); border: 1.5px solid #EF6351; border-radius: 12px; padding: 14px 18px; margin-bottom: 20px;">
                <div style="font-weight: 800; color: #EF6351; margin-bottom: 4px; font-family: var(--font-heading);">
                    ✨ Continuous Adaptation Triggered ({diff.get('version_from', 'v1')} ➔ {diff.get('version_to', 'v2')})
                </div>
                <div style="font-size: 0.9rem; line-height: 1.5;">
                    <b>Trigger:</b> <i>"{diff.get('trigger_message', '')}"</i><br/>
                    <b>Engine Action:</b> {diff.get('explanation', '')}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Render Dynamic Horizontal Stage Track Visual
    stage_steps_html = []
    has_active_stage = False

    for idx, stage in enumerate(roadmap.stages, start=1):
        is_completed = (stage.completion_status == "completed") or (stage.milestone and stage.milestone.completed)
        
        if is_completed:
            status_class = "done"
            node_label = "✓"
            sub_label = f"Done · ~{stage.estimated_hours}h"
        elif not has_active_stage or stage.completion_status == "in_progress":
            status_class = "current"
            node_label = str(idx)
            sub_label = f"Active · ~{stage.estimated_hours}h"
            has_active_stage = True
        else:
            status_class = "locked"
            node_label = str(idx)
            sub_label = f"Locked · ~{stage.estimated_hours}h"

        stage_steps_html.append(
            f"""
            <div class="stage-step {status_class}">
                <div class="stage-node">{node_label}</div>
                <div class="stage-step-title">{stage.title}</div>
                <div class="stage-step-sub">{sub_label}</div>
            </div>
            """
        )

    st.markdown(
        f"""
        <div class="glass-card" style="padding: 16px 20px; margin-bottom: 24px;">
            <div style="font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: var(--c-coral); margin-bottom: 8px;">
                Sequential Competency Progression ({len(roadmap.stages)} Stages)
            </div>
            <div class="track-wrap">
                {"".join(stage_steps_html)}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Render Planning Rationale
    if roadmap.rationale:
        with st.expander("💡 Roadmap Planning Rationale & Prerequisite Strategy", expanded=False):
            for rat in roadmap.rationale:
                st.markdown(f"- {rat}")

    # Render Ordered Detailed Stages
    for idx, stage in enumerate(roadmap.stages, start=1):
        is_bottleneck = "prerequisite bottleneck" in stage.rationale.lower()
        badge_html = '<span class="badge badge-bottleneck">Prerequisite Focus</span>' if is_bottleneck else f'<span class="badge badge-jade">Stage {idx}</span>'

        with st.container():
            st.markdown(
                f"""
                <div class="stage-card {'stage-bottleneck' if is_bottleneck else ''}">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 6px;">
                        <div>
                            {badge_html}
                            <h4 style="margin: 8px 0 4px 0;">{stage.title}</h4>
                        </div>
                        <div style="text-align: right;">
                            <span style="font-size: 0.85rem; font-weight: 700; color: var(--c-coral);">~{stage.estimated_hours} hrs</span>
                        </div>
                    </div>
                    <div style="font-size: 0.9rem; margin-bottom: 10px; opacity: 0.9;">
                        {stage.objective}
                    </div>
                    <div style="font-size: 0.8rem; font-style: italic; opacity: 0.8;">
                        <b>Why this is here:</b> {stage.rationale}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Milestones & Resources
            m_col, r_col = st.columns([1, 1])
            
            with m_col:
                st.markdown(f"**🎯 {stage.milestone.title}**")
                for crit in stage.milestone.success_criteria:
                    st.checkbox(f"{crit}", key=f"crit_{stage.stage_id}_{crit[:15]}")

            with r_col:
                st.markdown("**📚 Recommended Learning Assets & Projects**")
                for res in stage.resources:
                    st.markdown(
                        f"""
                        <div class="resource-pill">
                            <div>
                                <span style="font-size: 0.72rem; background: rgba(239,99,81,0.18); color: var(--c-coral); padding: 2px 6px; border-radius: 4px; font-weight: 700; text-transform: uppercase;">{res.resource_type}</span>
                                <div style="margin-top: 4px;"><a href="{res.url}" target="_blank">{res.title}</a></div>
                                <div style="font-size: 0.75rem; opacity: 0.7;">Provider: {res.provider} • Effort: ~{res.estimated_effort_hours}h</div>
                            </div>
                            <div>
                                <span class="badge badge-jade" style="font-size: 0.7rem;">{int(res.relevance_score * 100)}% Match</span>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
            st.divider()
