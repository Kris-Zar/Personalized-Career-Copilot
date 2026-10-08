import streamlit as st
from core.storage.store import InMemoryStore
from ui.components.radar_chart import render_gap_charts

def render_results_view(store: InMemoryStore):
    st.subheader("📊 Skill-Gap & Prerequisite Bottleneck Analysis")
    st.caption("Step 4 of 6: Evidence-based breakdown comparing self-reported claims against demonstrated diagnostic test performance.")

    gap_rep = store.gap_report
    if not gap_rep or not gap_rep.comparison_data:
        st.warning("⚠️ No diagnostic assessment results available yet. Please complete Step 3 (Assessment) first.")
        if st.button("Go to Assessment"):
            st.session_state["active_tab"] = "📝 3. Assessment"
            st.rerun()
        return

    # Metrics Summary Row
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-card-label">Skills Analyzed</div>
                <div class="metric-card-val">{len(gap_rep.comparison_data)}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with m2:
        st.markdown(
            f"""
            <div class="metric-card success">
                <div class="metric-card-label">Adequate Competencies</div>
                <div class="metric-card-val" style="color: var(--c-jade);">{len(gap_rep.adequate_skills)}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with m3:
        st.markdown(
            f"""
            <div class="metric-card gold">
                <div class="metric-card-label">Needs Improvement</div>
                <div class="metric-card-val" style="color: var(--c-tangerine);">{len(gap_rep.needs_improvement_skills)}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with m4:
        st.markdown(
            f"""
            <div class="metric-card urgent">
                <div class="metric-card-label">Bottleneck Deficits</div>
                <div class="metric-card-val" style="color: var(--c-coral);">{len(gap_rep.unresolved_prerequisites)}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Dynamic Prerequisite Bottleneck Deficit Callout
    if gap_rep.unresolved_prerequisites:
        bottleneck_items = [
            item for item in gap_rep.comparison_data if item.skill_id in gap_rep.unresolved_prerequisites
        ]
        
        alerts_html = []
        for b_item in bottleneck_items:
            claimed_pct = int(b_item.self_reported * 100)
            demo_pct = int(b_item.demonstrated * 100)
            target_pct = int(b_item.target * 100)
            alerts_html.append(
                f"""
                <div class="deficit-alert">
                    <div class="deficit-alert-title">
                        🚨 Critical Bottleneck Detected: {b_item.skill_name}
                    </div>
                    <div class="deficit-alert-body">
                        You self-reported <b>{claimed_pct}% proficiency</b> in {b_item.skill_name}, but demonstrated test score was <b>{demo_pct}%</b> (Target Required: <b>{target_pct}%</b>).
                        Because this competency is a strict prerequisite for downstream modules, the roadmap engine has prioritized resolving this foundational bottleneck first.
                    </div>
                </div>
                """
            )
        st.markdown("".join(alerts_html), unsafe_allow_html=True)

    # Dynamic Competency Progress Bars (Weakest First)
    sorted_items = sorted(
        gap_rep.comparison_data,
        key=lambda x: (x.status != "weak", x.status != "needs_improvement", x.demonstrated)
    )

    skill_rows_html = []
    for item in sorted_items:
        pct = int(item.demonstrated * 100)
        if item.status == "adequate":
            bar_color = "var(--c-jade)"
            text_color = "var(--c-jade)"
            status_label = "strong"
        elif item.status == "needs_improvement":
            bar_color = "var(--c-cerulean)"
            text_color = "var(--c-cerulean)"
            status_label = "building"
        elif item.status == "weak":
            bar_color = "var(--c-coral)"
            text_color = "var(--c-coral)"
            status_label = "weak"
        else:
            bar_color = "rgba(255,255,255,0.2)"
            text_color = "var(--text-muted)"
            status_label = "unassessed"

        skill_rows_html.append(
            f"""
            <div class="skill-row">
                <span class="skill-name">{item.skill_name}</span>
                <div class="skill-track"><div class="skill-fill" style="width: {max(5, pct)}%; background: {bar_color};"></div></div>
                <span class="skill-pct" style="color: {text_color};">{pct}% · {status_label}</span>
            </div>
            """
        )

    st.markdown(
        f"""
        <div class="glass-card">
            <div class="panel-heading">Assessed Competencies (Weakest-First Prioritization)</div>
            {"".join(skill_rows_html)}
        </div>
        """,
        unsafe_allow_html=True
    )

    # Plotly Comparison Radar Chart
    render_gap_charts(gap_rep.comparison_data)

    # Detailed Audit Table
    st.markdown("#### 📋 Detailed Competency Audit Table")
    table_data = []
    for item in gap_rep.comparison_data:
        table_data.append({
            "Skill / Competency": item.skill_name,
            "Self-Report (Claimed)": f"{int(item.self_reported * 100)}%",
            "Demonstrated (Evidence)": f"{int(item.demonstrated * 100)}%",
            "Target Required": f"{int(item.target * 100)}%",
            "Gap Deficit": f"{int(item.gap * 100)}%",
            "Status": item.status.upper(),
            "Prerequisite Bottleneck?": "🚨 YES" if item.is_bottleneck else "No"
        })

    st.dataframe(table_data, use_container_width=True)

    if st.button("🗺️ See Updated Personalized Roadmap ➔", type="primary", use_container_width=True):
        st.session_state["active_tab"] = "🗺️ 5. Personalized Roadmap"
        st.rerun()
