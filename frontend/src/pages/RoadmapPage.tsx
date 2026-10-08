import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { Roadmap } from '../types';

export const RoadmapPage: React.FC = () => {
  const navigate = useNavigate();
  const [roadmap, setRoadmap] = useState<Roadmap | null>(null);
  const [versions, setVersions] = useState<Record<number, Roadmap>>({});
  const [selectedVersion, setSelectedVersion] = useState<number>(1);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadRoadmaps();
  }, []);

  const loadRoadmaps = async () => {
    try {
      const vers = await api.getRoadmapVersions();
      setVersions(vers);
      const versKeys = Object.keys(vers).map(Number);
      if (versKeys.length > 0) {
        const latest = Math.max(...versKeys);
        setSelectedVersion(latest);
        setRoadmap(vers[latest]);
      } else {
        const current = await api.getRoadmap();
        if (current) {
          setRoadmap(current);
          setSelectedVersion(current.version);
        }
      }
    } catch (err) {
      console.error('Failed to load roadmap:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleVersionChange = (v: number) => {
    setSelectedVersion(v);
    if (versions[v]) {
      setRoadmap(versions[v]);
    } else {
      api.getRoadmap(v).then((r) => {
        if (r) setRoadmap(r);
      });
    }
  };

  if (loading) {
    return <div className="screen-frame">Loading personalized learning roadmap...</div>;
  }

  if (!roadmap || !roadmap.stages || roadmap.stages.length === 0) {
    return (
      <div className="screen-frame">
        <div className="screen-tag">
          <span>05 · Personalized Learning Roadmap</span>
          <span className="screen-pill">Step 5 of 6</span>
        </div>
        <div className="diff-box">
          <strong>⚠️ No roadmap generated yet.</strong>
          Complete Step 3 (Assessment) to generate your personalized learning plan.
        </div>
        <button className="btn btn-primary" onClick={() => navigate('/assessment')}>
          Go to Assessment ➔
        </button>
      </div>
    );
  }

  const versionList = Object.keys(versions).map(Number).sort((a, b) => a - b);
  const adaptationDiff = roadmap.adaptation_diff;

  return (
    <div className="screen-frame">
      <div className="screen-tag">
        <span>05 · Personalized Learning Roadmap</span>
        <span className="screen-pill">Step 5 of 6</span>
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '14px', marginBottom: '16px' }}>
        <div>
          <h2 style={{ fontFamily: 'Space Grotesk, sans-serif', fontSize: '20px', fontWeight: 800, color: 'var(--text-primary)', margin: '0 0 4px 0' }}>
            Personalized Learning Roadmap (Version {roadmap.version})
          </h2>
          <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
            Generated: {roadmap.generated_at.slice(0, 10)} · Total Estimated Effort: ~{Math.round(roadmap.total_estimated_hours)} hours
          </div>
        </div>

        {versionList.length > 1 && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-secondary)' }}>Version History:</span>
            {versionList.map((v) => (
              <button
                key={v}
                className={`btn btn-sm ${selectedVersion === v ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => handleVersionChange(v)}
              >
                v{v} {v === Math.max(...versionList) ? '(Active)' : ''}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Adaptation Diff Banner */}
      {adaptationDiff && (
        <div className="diff-box" style={{ marginBottom: '20px' }}>
          <strong>✨ Continuous Adaptation Triggered ({adaptationDiff.version_from || 'v1'} ➔ {adaptationDiff.version_to || 'v2'})</strong>
          <b>Feedback Trigger:</b> <i>"{adaptationDiff.trigger_message || ''}"</i><br />
          <b>Engine Action:</b> {adaptationDiff.explanation || ''}
        </div>
      )}

      {/* Connected Horizontal Stage Track */}
      <div className="pf-panel" style={{ padding: '20px', marginBottom: '24px' }}>
        <div style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--c-coral)', marginBottom: '16px' }}>
          Sequential Competency Progression ({roadmap.stages.length} Stages)
        </div>

        <div className="track-container">
          <div className="track">
            {roadmap.stages.map((stage, idx) => {
              const isDone = stage.completion_status === 'completed' || stage.milestone?.completed;
              const isCurrent = !isDone && idx === 0;
              const statusClass = isDone ? 'done' : isCurrent ? 'current' : 'locked';
              const nodeLabel = isDone ? '✓' : String(idx + 1);
              const subLabel = isDone ? `Done · ~${stage.estimated_hours}h` : `~${stage.estimated_hours}h`;

              return (
                <div key={stage.stage_id} className={`stage ${statusClass}`}>
                  <div className="node">{nodeLabel}</div>
                  <p className="stage-title">{stage.title}</p>
                  <p className="stage-sub">{subLabel}</p>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Detailed Ordered Stage Cards */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', marginBottom: '24px' }}>
        {roadmap.stages.map((stage, idx) => {
          const isBottleneck =
            stage.rationale.toLowerCase().includes('bottleneck') ||
            stage.rationale.toLowerCase().includes('prerequisite');

          return (
            <div
              key={stage.stage_id}
              className={`stage-card ${isBottleneck ? 'bottleneck' : ''}`}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                <div>
                  {isBottleneck ? (
                    <span className="badge coral" style={{ marginBottom: '6px' }}>
                      🔒 Prerequisite Bottleneck
                    </span>
                  ) : (
                    <span className="badge jade" style={{ marginBottom: '6px' }}>
                      Stage {idx + 1}
                    </span>
                  )}
                  <h3 style={{ fontFamily: 'Space Grotesk, sans-serif', fontWeight: 800, fontSize: '17px', color: 'var(--text-primary)', marginTop: '4px' }}>
                    {stage.title}
                  </h3>
                </div>
                <span style={{ fontSize: '13px', fontWeight: 700, color: 'var(--c-coral)' }}>
                  ~{stage.estimated_hours} hrs
                </span>
              </div>

              <p style={{ fontSize: '13px', color: 'var(--text-primary)', marginBottom: '8px' }}>
                {stage.objective}
              </p>

              <p style={{ fontSize: '12px', color: 'var(--text-secondary)', fontStyle: 'italic', marginBottom: '14px' }}>
                <b>Rationale:</b> {stage.rationale}
              </p>

              {/* Resources */}
              {stage.resources && stage.resources.length > 0 && (
                <div style={{ marginBottom: '14px' }}>
                  <div style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-secondary)', marginBottom: '6px' }}>
                    Curated Learning Resources ({stage.resources.length})
                  </div>
                  {stage.resources.map((res) => (
                    <div key={res.resource_id} className="resource-item">
                      <div>
                        <div style={{ fontWeight: 700, color: 'var(--text-primary)', fontSize: '13px' }}>
                          {res.title}
                        </div>
                        <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                          {res.provider} · {res.resource_type.toUpperCase()} · ~{res.estimated_effort_hours}h
                        </div>
                      </div>
                      <a href={res.url} target="_blank" rel="noopener noreferrer" className="res-link">
                        Launch ➔
                      </a>
                    </div>
                  ))}
                </div>
              )}

              {/* Milestone Checkpoints */}
              {stage.milestone?.success_criteria && stage.milestone.success_criteria.length > 0 && (
                <div style={{ background: 'var(--bg-paper)', borderRadius: '8px', padding: '12px 14px', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--c-coral)', marginBottom: '6px' }}>
                    🎯 Milestone Checkpoints: {stage.milestone.title}
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    {stage.milestone.success_criteria.map((crit, cIdx) => (
                      <label key={cIdx} style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px', color: 'var(--text-primary)', cursor: 'pointer' }}>
                        <input type="checkbox" style={{ accentColor: 'var(--c-coral)' }} />
                        <span>{crit}</span>
                      </label>
                    ))}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      <div style={{ textAlign: 'right' }}>
        <button className="btn btn-primary" onClick={() => navigate('/dashboard')}>
          Go to Master Dashboard ➔
        </button>
      </div>
    </div>
  );
};
