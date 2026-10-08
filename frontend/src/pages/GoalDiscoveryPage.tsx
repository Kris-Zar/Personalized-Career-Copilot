import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { GoalState, GoalCatalogItem } from '../types';

export const GoalDiscoveryPage: React.FC = () => {
  const navigate = useNavigate();
  const [goalState, setGoalState] = useState<GoalState | null>(null);
  const [catalog, setCatalog] = useState<GoalCatalogItem[]>([]);
  const [prompt, setPrompt] = useState(
    'I want to become an industry-ready Data Scientist within 6 months. I have about 8 hours per week to study.'
  );
  const [loading, setLoading] = useState(false);
  const [source, setSource] = useState<string>('gemini');

  useEffect(() => {
    api.getGoal().then((g) => {
      if (g) setGoalState(g);
    });
    api.getGoalCatalog().then((cat) => setCatalog(cat));
  }, []);

  const handleExtract = async () => {
    setLoading(true);
    try {
      const res = await api.extractGoal(prompt);
      setGoalState(res.goal_state);
      setSource(res.source);
    } catch (err: any) {
      alert(`Extraction failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectTrack = async (catItem: GoalCatalogItem) => {
    try {
      const g = await api.selectGoal(catItem.goal_id, catItem.target_role, catItem.recommended_timeline_months, catItem.recommended_weekly_hours);
      setGoalState(g);
    } catch (err: any) {
      alert(`Selection failed: ${err.message}`);
    }
  };

  return (
    <div className="screen-frame">
      <div className="screen-tag">
        <span>02 · Conversational Goal Discovery</span>
        <span className="screen-pill">Step 2 of 6</span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px', marginBottom: '24px' }}>
        <div>
          <div className="chat-thread">
            <div className="msg assistant">
              👋 Hello! I'm your XCL PathFinder career copilot. State your target role, available weekly hours, and timeline to activate your personalized learning track.
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Your Career Goal Statement:</label>
            <textarea
              className="form-textarea"
              rows={3}
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="e.g. I want to transition into Machine Learning Engineering within 6 months..."
            />
          </div>

          <button
            className="btn btn-primary"
            onClick={handleExtract}
            disabled={loading}
            style={{ width: '100%' }}
          >
            {loading ? '⚡ Extracting with Gemini AI...' : 'Send & Extract Goal with Gemini AI ➔'}
          </button>
        </div>

        <div>
          <div className="pf-panel" style={{ height: '100%' }}>
            <div className="pf-panel-title">
              <span>Active Store State</span>
              {source === 'gemini' ? (
                <span className="badge jade">⚡ Gemini 3.6 Flash</span>
              ) : (
                <span className="badge tangerine">Deterministic Engine</span>
              )}
            </div>

            <div style={{ fontSize: '13px', lineHeight: 1.8, color: 'var(--text-primary)' }}>
              <div><b>Target Role:</b> {goalState?.target_role || 'Data Scientist (Pending)'}</div>
              <div><b>Timeline:</b> {goalState?.timeline_months || 6} months</div>
              <div><b>Weekly Study:</b> {goalState?.weekly_hours || 8.0} hrs/week</div>
              <div><b>Status:</b> {goalState?.active ? 'Active in Authoritative Store' : 'Pending Extraction'}</div>
            </div>

            {goalState?.active && (
              <div className="diff-box" style={{ marginTop: '16px', background: 'var(--c-jade-tint)', borderColor: 'var(--c-jade)', borderLeftColor: 'var(--c-jade)' }}>
                <strong style={{ color: 'var(--c-jade)' }}>🎯 Goal Checkpoint Activated</strong>
                Ready for diagnostic knowledge assessment.
              </div>
            )}
          </div>
        </div>
      </div>

      <h3 style={{ fontFamily: 'Space Grotesk, sans-serif', fontSize: '15px', fontWeight: 700, margin: '20px 0 12px 0' }}>
        Available Career Tracks in Catalog
      </h3>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '14px', marginBottom: '24px' }}>
        {catalog.map((c) => {
          const isActive = goalState?.goal_id === c.goal_id;
          return (
            <div
              key={c.goal_id}
              className="pf-panel"
              style={{
                borderColor: isActive ? 'var(--c-coral)' : 'var(--border-subtle)',
                borderWidth: isActive ? '2px' : '1px',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                height: '160px',
              }}
            >
              <div>
                <div style={{ fontWeight: 700, fontSize: '14px', color: isActive ? 'var(--c-coral)' : 'var(--text-primary)' }}>
                  {c.title}
                </div>
                <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '4px' }}>
                  {c.description.slice(0, 85)}...
                </div>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '11px', color: 'var(--c-tangerine)', fontWeight: 700 }}>
                  ⏱️ {c.recommended_timeline_months}m · {c.recommended_weekly_hours}h/wk
                </span>
                <button
                  className={`btn btn-sm ${isActive ? 'btn-primary' : 'btn-secondary'}`}
                  onClick={() => handleSelectTrack(c)}
                >
                  {isActive ? '✓ Active' : 'Select'}
                </button>
              </div>
            </div>
          );
        })}
      </div>

      <div style={{ textAlign: 'right' }}>
        <button className="btn btn-primary" onClick={() => navigate('/assessment')}>
          Proceed to Diagnostic Assessment ➔
        </button>
      </div>
    </div>
  );
};
