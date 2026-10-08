import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { LearnerProfile } from '../types';

export const ProfilePage: React.FC = () => {
  const navigate = useNavigate();
  const [profile, setProfile] = useState<LearnerProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [name, setName] = useState('');
  const [role, setRole] = useState('');
  const [weeklyHours, setWeeklyHours] = useState(8);
  const [timelineMonths, setTimelineMonths] = useState(6);
  const [skills, setSkills] = useState<Record<string, number>>({
    py_core: 0.5,
    math_prob_stats: 0.5,
    ml_foundations: 0.4,
    dl_neural_nets: 0.2,
    ml_ops: 0.2,
  });

  useEffect(() => {
    api
      .getProfile()
      .then((data) => {
        setProfile(data);
        setName(data.name || 'Alex Chen');
        setRole(data.current_role || 'Biology Student');
        setWeeklyHours(data.weekly_hours || 8);
        setTimelineMonths(data.timeline_months || 6);
        if (data.self_reported_skills && Object.keys(data.self_reported_skills).length > 0) {
          setSkills({ ...skills, ...data.self_reported_skills });
        }
      })
      .catch((err) => console.error('Failed to load profile:', err))
      .finally(() => setLoading(false));
  }, []);

  const handleSkillChange = (key: string, val: number) => {
    setSkills((prev) => ({ ...prev, [key]: val }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await api.updateProfile({
        name,
        current_role: role,
        weekly_hours: Number(weeklyHours),
        timeline_months: Number(timelineMonths),
        self_reported_skills: skills,
        interests: ['Machine Learning', 'Data Science', 'Applied AI'],
        content_preferences: ['projects', 'interactive', 'videos'],
      });
      navigate('/goal');
    } catch (err: any) {
      alert(`Failed to save profile: ${err.message}`);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="screen-frame">Loading profile baseline...</div>;
  }

  return (
    <div className="screen-frame">
      <div className="screen-tag">
        <span>01 · Learner Profile &amp; Self-Reported Baseline</span>
        <span className="screen-pill">Step 1 of 6</span>
      </div>

      <form onSubmit={handleSubmit}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px', marginBottom: '20px' }}>
          <div className="form-group">
            <label className="form-label">Full Name</label>
            <input
              type="text"
              className="form-input"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Alex Chen"
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label">Current Background / Role</label>
            <input
              type="text"
              className="form-input"
              value={role}
              onChange={(e) => setRole(e.target.value)}
              placeholder="e.g. Biology Student / Software Engineer"
              required
            />
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px', marginBottom: '24px' }}>
          <div className="form-group">
            <label className="form-label">Available Weekly Study Commitment: {weeklyHours} hrs/week</label>
            <input
              type="range"
              min="2"
              max="40"
              step="1"
              value={weeklyHours}
              onChange={(e) => setWeeklyHours(Number(e.target.value))}
              style={{ width: '100%', accentColor: 'var(--c-coral)' }}
            />
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--text-secondary)' }}>
              <span>2 hrs (Light)</span>
              <span>8 hrs (Standard)</span>
              <span>20+ hrs (Intensive)</span>
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Target Completion Timeline: {timelineMonths} Months</label>
            <input
              type="range"
              min="1"
              max="24"
              step="1"
              value={timelineMonths}
              onChange={(e) => setTimelineMonths(Number(e.target.value))}
              style={{ width: '100%', accentColor: 'var(--c-coral)' }}
            />
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--text-secondary)' }}>
              <span>1 Mo</span>
              <span>6 Mos</span>
              <span>24 Mos</span>
            </div>
          </div>
        </div>

        <div className="pf-panel" style={{ marginBottom: '24px' }}>
          <div className="pf-panel-title">
            <span>Self-Reported Skill Baseline (Signal 5)</span>
            <span className="pf-panel-tag">Initial Estimate</span>
          </div>
          <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '16px' }}>
            Rate your current comfort level across foundational topics. We will use diagnostic testing in Step 3 to calibrate your actual demonstrated competency.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            {[
              { id: 'py_core', label: 'Python Programming & Software Engineering' },
              { id: 'math_prob_stats', label: 'Probability & Applied Statistics' },
              { id: 'ml_foundations', label: 'Classical Machine Learning Foundations' },
              { id: 'dl_neural_nets', label: 'Deep Learning & Neural Networks' },
              { id: 'ml_ops', label: 'MLOps, Model Serving & Deployment' },
            ].map((item) => (
              <div key={item.id} style={{ display: 'grid', gridTemplateColumns: '260px 1fr 60px', alignItems: 'center', gap: '14px' }}>
                <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>{item.label}</span>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={skills[item.id] || 0}
                  onChange={(e) => handleSkillChange(item.id, parseFloat(e.target.value))}
                  style={{ accentColor: 'var(--c-coral)' }}
                />
                <span style={{ fontFamily: 'IBM Plex Mono, monospace', fontSize: '12px', fontWeight: 700, textAlign: 'right', color: 'var(--c-coral)' }}>
                  {Math.round((skills[item.id] || 0) * 100)}%
                </span>
              </div>
            ))}
          </div>
        </div>

        <div style={{ textAlign: 'right' }}>
          <button type="submit" className="btn btn-primary" disabled={saving}>
            {saving ? 'Saving...' : 'Continue to Goal Discovery ➔'}
          </button>
        </div>
      </form>
    </div>
  );
};
