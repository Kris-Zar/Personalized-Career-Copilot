import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { GapReport } from '../types';

export const ResultsPage: React.FC = () => {
  const navigate = useNavigate();
  const [gapReport, setGapReport] = useState<GapReport | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .getGaps()
      .then((data) => setGapReport(data))
      .catch((err) => console.error('Failed to load gap report:', err))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="screen-frame">Loading diagnostic results and gap analysis...</div>;
  }

  if (!gapReport || !gapReport.comparison_data || gapReport.comparison_data.length === 0) {
    return (
      <div className="screen-frame">
        <div className="screen-tag">
          <span>04 · Skill Gap &amp; Prerequisite Analysis</span>
          <span className="screen-pill">Step 4 of 6</span>
        </div>
        <div className="diff-box">
          <strong>⚠️ No diagnostic assessment results available yet.</strong>
          Please complete Step 3 (Assessment) to calibrate your knowledge baseline.
        </div>
        <button className="btn btn-primary" onClick={() => navigate('/assessment')}>
          Go to Assessment ➔
        </button>
      </div>
    );
  }

  const comparisonData = gapReport.comparison_data;
  // Sort weakest-first
  const sortedItems = [...comparisonData].sort((a, b) => {
    if (a.status === 'weak' && b.status !== 'weak') return -1;
    if (a.status !== 'weak' && b.status === 'weak') return 1;
    return a.demonstrated - b.demonstrated;
  });

  const bottlenecks = comparisonData.filter((item) =>
    gapReport.unresolved_prerequisites.includes(item.skill_id)
  );

  return (
    <div className="screen-frame">
      <div className="screen-tag">
        <span>04 · Skill Gap &amp; Prerequisite Analysis</span>
        <span className="screen-pill">Step 4 of 6</span>
      </div>

      <div style={{ marginBottom: '18px' }}>
        <h2 style={{ fontFamily: 'Space Grotesk, sans-serif', fontSize: '20px', fontWeight: 800, color: 'var(--text-primary)', margin: '0 0 4px 0' }}>
          Assessment Summary
        </h2>
        <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
          Demonstrated evidence scored from diagnostic items against target {gapReport.target_role} requirements.
        </p>
      </div>

      {/* 4-Metric Grid */}
      <div className="metrics-grid">
        <div className="pf-metric">
          <div className="pf-metric-label">Skills Analyzed</div>
          <div className="pf-metric-val">{comparisonData.length}</div>
        </div>

        <div className="pf-metric success">
          <div className="pf-metric-label">Adequate / Mastered</div>
          <div className="pf-metric-val" style={{ color: 'var(--c-jade)' }}>
            {gapReport.adequate_skills.length}
          </div>
        </div>

        <div className="pf-metric">
          <div className="pf-metric-label">Needs Improvement</div>
          <div className="pf-metric-val" style={{ color: 'var(--c-cerulean)' }}>
            {gapReport.needs_improvement_skills.length}
          </div>
        </div>

        <div className="pf-metric urgent">
          <div className="pf-metric-label">Bottleneck Deficits</div>
          <div className="pf-metric-val" style={{ color: 'var(--c-coral)' }}>
            {gapReport.unresolved_prerequisites.length}
          </div>
        </div>
      </div>

      {/* Dynamic Deficit Alert Box */}
      {bottlenecks.length > 0 &&
        bottlenecks.map((b) => (
          <div key={b.skill_id} className="diff-box">
            <strong>🚨 Claimed vs Demonstrated Deficit Detected: {b.skill_name}</strong>
            You self-reported <b>{Math.round(b.self_reported * 100)}% proficiency</b> in {b.skill_name}, but demonstrated test score was <b>{Math.round(b.demonstrated * 100)}%</b> (Target Required: <b>{Math.round(b.target * 100)}%</b>). The roadmap engine has prioritized foundational competencies in Stage 1 to resolve this bottleneck before downstream modules.
          </div>
        ))}

      {/* Assessed Competencies (Weakest-First Prioritization) */}
      <div className="pf-panel" style={{ marginBottom: '24px' }}>
        <div className="pf-panel-title">
          <span>Assessed Competencies (Weakest-First)</span>
          <span className="pf-panel-tag">Calibrated Evidence</span>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {sortedItems.map((item) => {
            const pct = Math.round(item.demonstrated * 100);
            let barColor = 'var(--c-coral)';
            let statusLabel = 'weak';
            if (item.status === 'adequate') {
              barColor = 'var(--c-jade)';
              statusLabel = 'strong';
            } else if (item.status === 'needs_improvement') {
              barColor = 'var(--c-cerulean)';
              statusLabel = 'building';
            }

            return (
              <div key={item.skill_id} className="skill-row">
                <span className="skill-name">{item.skill_name}</span>
                <div className="skill-track">
                  <div
                    className="skill-fill"
                    style={{ width: `${Math.max(6, pct)}%`, background: barColor }}
                  ></div>
                </div>
                <span className="skill-pct" style={{ color: barColor }}>
                  {pct}% · {statusLabel}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Comparison Table */}
      <div className="pf-panel" style={{ marginBottom: '24px' }}>
        <div className="pf-panel-title">
          <span>Competency Calibration Audit Table</span>
        </div>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px', textAlign: 'left' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid var(--border-subtle)', color: 'var(--text-secondary)' }}>
                <th style={{ padding: '8px 12px' }}>Skill Competency</th>
                <th style={{ padding: '8px 12px' }}>Self-Reported</th>
                <th style={{ padding: '8px 12px' }}>Demonstrated Evidence</th>
                <th style={{ padding: '8px 12px' }}>Target Proficiency</th>
                <th style={{ padding: '8px 12px' }}>Status</th>
              </tr>
            </thead>
            <tbody>
              {sortedItems.map((item) => (
                <tr key={item.skill_id} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                  <td style={{ padding: '10px 12px', fontWeight: 600 }}>{item.skill_name}</td>
                  <td style={{ padding: '10px 12px', fontFamily: 'IBM Plex Mono, monospace' }}>
                    {Math.round(item.self_reported * 100)}%
                  </td>
                  <td style={{ padding: '10px 12px', fontFamily: 'IBM Plex Mono, monospace', fontWeight: 700 }}>
                    {Math.round(item.demonstrated * 100)}%
                  </td>
                  <td style={{ padding: '10px 12px', fontFamily: 'IBM Plex Mono, monospace' }}>
                    {Math.round(item.target * 100)}%
                  </td>
                  <td style={{ padding: '10px 12px' }}>
                    <span
                      className={`badge ${
                        item.status === 'adequate' ? 'jade' : item.status === 'needs_improvement' ? 'cerulean' : 'coral'
                      }`}
                    >
                      {item.status.toUpperCase()}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div style={{ textAlign: 'right' }}>
        <button className="btn btn-primary" onClick={() => navigate('/roadmap')}>
          See Updated Roadmap ➔
        </button>
      </div>
    </div>
  );
};
