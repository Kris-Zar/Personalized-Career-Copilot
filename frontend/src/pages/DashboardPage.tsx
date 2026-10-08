import React, { useEffect, useState } from 'react';
import { api } from '../api/client';
import { DashboardData, Roadmap, KnowledgeState } from '../types';

export const DashboardPage: React.FC = () => {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [chatInput, setChatInput] = useState('');
  const [chatHistory, setChatHistory] = useState<Array<{ role: string; content: string }>>([]);
  const [sending, setSending] = useState(false);
  const [activeTab, setActiveTab] = useState<'roadmap' | 'log'>('roadmap');

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      const d = await api.getDashboard();
      setData(d);
      setChatHistory(d.chat_history || []);
    } catch (err) {
      console.error('Failed to load dashboard:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSendMessage = async (text?: string) => {
    const query = (text || chatInput).trim();
    if (!query || sending) return;

    setChatInput('');
    setSending(true);

    const userMsg = { role: 'user', content: query };
    setChatHistory((prev) => [...prev, userMsg]);

    try {
      const res = await api.tutorChat(query);
      const assistantMsg = { role: 'assistant', content: res.reply };
      setChatHistory((prev) => [...prev, assistantMsg]);

      // If continuous adaptation triggered, refresh dashboard to show Roadmap v2
      if (res.is_adaptation) {
        await loadDashboard();
      }
    } catch (err: any) {
      const errorMsg = { role: 'assistant', content: `⚠️ Error: ${err.message}` };
      setChatHistory((prev) => [...prev, errorMsg]);
    } finally {
      setSending(false);
    }
  };

  if (loading) {
    return <div className="screen-frame">Loading master dashboard cockpit...</div>;
  }

  if (!data) {
    return <div className="screen-frame">Failed to load dashboard telemetry.</div>;
  }

  const kStates = data.knowledge_states || [];
  const currentRoadmap = data.current_roadmap;
  const unresolvedPrereqs = data.gap_report?.unresolved_prerequisites || [];

  return (
    <div className="screen-frame">
      <div className="screen-tag">
        <span>06 · Master Dashboard &amp; Cockpit</span>
        <span className="screen-pill">Live Hub</span>
      </div>

      {/* Top Greeting */}
      <div style={{ marginBottom: '18px' }}>
        <h1 style={{ fontFamily: 'Space Grotesk, sans-serif', fontSize: '22px', fontWeight: 800, color: 'var(--text-primary)', margin: '0 0 4px 0' }}>
          Welcome back, {data.learner_name || 'Learner'}
        </h1>
        <div style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
          Goal: <b>{data.target_role}</b> · <b>{data.timeline_months} months</b> · <b>{data.weekly_hours} hrs/week</b>
        </div>
      </div>

      {/* 3 Metric Cards */}
      <div className="metrics-grid" style={{ gridTemplateColumns: 'repeat(3, 1fr)' }}>
        <div className="pf-metric">
          <div className="pf-metric-label">Roadmap Progress</div>
          <div className="pf-metric-val">{data.progress_percentage}%</div>
        </div>

        <div className="pf-metric success">
          <div className="pf-metric-label">Skills Assessed</div>
          <div className="pf-metric-val" style={{ color: 'var(--c-jade)' }}>
            {data.skills_assessed_count}
          </div>
        </div>

        <div className="pf-metric urgent">
          <div className="pf-metric-label">Weak Prerequisites</div>
          <div className="pf-metric-val" style={{ color: 'var(--c-coral)' }}>
            {data.weak_prerequisites_count}
          </div>
        </div>
      </div>

      {/* Demonstrated Competency Baseline Panel */}
      <div className="pf-panel" style={{ marginBottom: '20px' }}>
        <div className="pf-panel-title">
          <span>Demonstrated Competency Baseline</span>
          <span className="pf-panel-tag">Evidence-Based</span>
        </div>

        {kStates.length === 0 ? (
          <div style={{ fontSize: '13px', color: 'var(--text-secondary)', padding: '6px 0' }}>
            No demonstrated evidence yet. Complete <b>Step 3 (Assessment)</b> to calibrate your competency baseline.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {kStates.map((ks) => {
              const pct = Math.round(ks.demonstrated_score * 100);
              let barColor = 'var(--c-coral)';
              let statusLabel = 'weak';
              if (ks.status === 'adequate') {
                barColor = 'var(--c-jade)';
                statusLabel = 'strong';
              } else if (ks.status === 'needs_improvement') {
                barColor = 'var(--c-cerulean)';
                statusLabel = 'building';
              }

              return (
                <div key={ks.skill_id} className="skill-row">
                  <span className="skill-name">{ks.skill_name}</span>
                  <div className="skill-track">
                    <div className="skill-fill" style={{ width: `${Math.max(6, pct)}%`, background: barColor }}></div>
                  </div>
                  <span className="skill-pct" style={{ color: barColor }}>
                    {pct}% · {statusLabel}
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Badges & Status Panel */}
      <div className="pf-panel" style={{ marginBottom: '24px' }}>
        <div className="pf-panel-title">Badges &amp; Milestone Status</div>
        <div className="badges-container">
          {kStates.length === 0 ? (
            <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
              No milestone badges unlocked yet. Complete diagnostic assessment to calibrate.
            </span>
          ) : (
            kStates.map((ks) => {
              if (unresolvedPrereqs.includes(ks.skill_id)) {
                return (
                  <span key={ks.skill_id} className="badge coral">
                    🔒 {ks.skill_name} · Bottleneck
                  </span>
                );
              }
              if (ks.status === 'adequate') {
                return (
                  <span key={ks.skill_id} className="badge jade">
                    ✓ {ks.skill_name} · Mastered
                  </span>
                );
              }
              if (ks.status === 'needs_improvement') {
                return (
                  <span key={ks.skill_id} className="badge tangerine">
                    ● {ks.skill_name} · Building
                  </span>
                );
              }
              return null;
            })
          )}
        </div>
      </div>

      {/* 2-Column Workspace: Left = Active Roadmap / Log, Right = AI Tutor & Adaptation Chat */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '20px' }}>
        {/* Left Column: Roadmap Overview */}
        <div>
          <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
            <button
              className={`btn btn-sm ${activeTab === 'roadmap' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setActiveTab('roadmap')}
            >
              🗺️ Active Roadmap {currentRoadmap ? `(v${currentRoadmap.version})` : ''}
            </button>
            <button
              className={`btn btn-sm ${activeTab === 'log' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setActiveTab('log')}
            >
              📋 Adaptation Info
            </button>
          </div>

          {activeTab === 'roadmap' ? (
            <div>
              {currentRoadmap?.adaptation_diff && (
                <div className="diff-box" style={{ marginBottom: '14px' }}>
                  <strong>✨ Continuous Adaptation Triggered (v{currentRoadmap.version})</strong>
                  {currentRoadmap.adaptation_diff.explanation || ''}
                </div>
              )}

              {currentRoadmap?.stages && currentRoadmap.stages.length > 0 ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  {currentRoadmap.stages.map((stage, idx) => (
                    <div key={stage.stage_id} className="stage-card" style={{ padding: '14px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontWeight: 700, fontSize: '14px', color: 'var(--text-primary)' }}>
                          Stage {idx + 1}: {stage.title}
                        </span>
                        <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--c-coral)' }}>
                          ~{stage.estimated_hours}h
                        </span>
                      </div>
                      <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px' }}>
                        {stage.objective}
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="pf-panel">No active roadmap. Complete assessment first.</div>
              )}
            </div>
          ) : (
            <div className="pf-panel">
              <div className="pf-panel-title">Adaptation Intent Engine</div>
              <p style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                XCL PathFinder actively parses 10 distinct learning signals in conversation: Difficulty, Pace, Time Constraint, Skip Request, Prior Knowledge, Preferences, Relevance, and Positive Progress. Send a chat query on the right to trigger real-time roadmap restructuring.
              </p>
            </div>
          )}
        </div>

        {/* Right Column: AI Tutor & Adaptation Chat */}
        <div className="pf-panel" style={{ display: 'flex', flexDirection: 'column', height: '520px' }}>
          <div className="pf-panel-title">
            <span>💬 AI Tutor &amp; Adaptation</span>
            <span className="badge jade">⚡ Gemini 3.6 Flash</span>
          </div>

          {/* Quick Prompts */}
          <div style={{ marginBottom: '12px' }}>
            <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--c-coral)', textTransform: 'uppercase', marginBottom: '6px' }}>
              ⚡ Quick Prompts:
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
              <button
                className="btn btn-secondary btn-sm"
                onClick={() => handleSendMessage('Why did you recommend Probability and Statistics before Machine Learning?')}
              >
                ❓ Why Probability first?
              </button>
              <button
                className="btn btn-secondary btn-sm"
                onClick={() => handleSendMessage('Probability is too difficult and I only have 30 minutes per day.')}
              >
                ⚡ 'Pace is too fast (30m/day)'
              </button>
              <button
                className="btn btn-secondary btn-sm"
                onClick={() => handleSendMessage('Can you explain Bayes Theorem in the context of machine learning?')}
              >
                📖 Explain Bayes Theorem
              </button>
            </div>
          </div>

          {/* Chat Messages */}
          <div className="chat-thread" style={{ flex: 1 }}>
            {chatHistory.length === 0 ? (
              <div className="msg assistant">
                👋 Hello! I'm your grounded AI tutor. Ask questions about your curriculum, milestones, or log difficulty to adapt your roadmap!
              </div>
            ) : (
              chatHistory.map((m, idx) => (
                <div key={idx} className={`msg ${m.role}`}>
                  {m.content}
                </div>
              ))
            )}
            {sending && <div className="msg assistant">Thinking with Gemini AI...</div>}
          </div>

          {/* Chat Input */}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage();
            }}
            style={{ display: 'flex', gap: '8px', marginTop: '10px' }}
          >
            <input
              type="text"
              className="form-input"
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              placeholder="Ask a question or log difficulty..."
              disabled={sending}
            />
            <button type="submit" className="btn btn-primary" disabled={sending || !chatInput.trim()}>
              Send
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};
