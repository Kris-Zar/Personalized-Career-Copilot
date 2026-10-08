import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { AssessmentItem } from '../types';

export const AssessmentPage: React.FC = () => {
  const navigate = useNavigate();
  const [items, setItems] = useState<AssessmentItem[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    api
      .getAssessment()
      .then((data) => setItems(data))
      .catch((err) => console.error('Failed to load assessment items:', err))
      .finally(() => setLoading(false));
  }, []);

  const handleSelectOption = (itemId: string, option: string) => {
    setAnswers((prev) => ({ ...prev, [itemId]: option }));
  };

  const handlePreFillAlex = () => {
    if (!items.length) return;
    const prefilled: Record<string, string> = {};
    items.forEach((item) => {
      // Alex: Good at Python, weak at Probability / Math
      if (item.skill_id === 'py_core') {
        prefilled[item.item_id] = item.correct_answer;
      } else {
        // Pick an incorrect option for math/stats to demonstrate bottleneck deficit
        const wrongOption = item.options.find((opt) => opt !== item.correct_answer) || item.options[0];
        prefilled[item.item_id] = wrongOption;
      }
    });
    setAnswers(prefilled);
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      const attemptsPayload = Object.entries(answers).map(([itemId, answer]) => ({
        item_id: itemId,
        answer,
      }));
      await api.completeAssessment(attemptsPayload.length > 0 ? attemptsPayload : undefined);
      navigate('/results');
    } catch (err: any) {
      alert(`Scoring failed: ${err.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return <div className="screen-frame">Loading diagnostic knowledge assessment...</div>;
  }

  if (!items.length) {
    return <div className="screen-frame">No assessment items available.</div>;
  }

  const currentItem = items[currentIndex];
  const progressPct = Math.round(((currentIndex + 1) / items.length) * 100);

  return (
    <div className="screen-frame">
      <div className="screen-tag">
        <span>03 · Diagnostic Knowledge Assessment</span>
        <span className="screen-pill">Step 3 of 6</span>
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-primary)' }}>
            Question {currentIndex + 1} of {items.length}
          </span>
          <span className="badge tangerine" style={{ textTransform: 'capitalize' }}>
            {currentItem.difficulty}
          </span>
          <span className="badge cerulean">{currentItem.skill_id}</span>
        </div>

        <button className="btn btn-secondary btn-sm" onClick={handlePreFillAlex}>
          💡 Pre-fill Sample Answers (Demonstrate Deficit)
        </button>
      </div>

      {/* Progress Bar */}
      <div className="skill-track" style={{ height: '6px', marginBottom: '20px' }}>
        <div className="skill-fill" style={{ width: `${progressPct}%`, background: 'var(--btn-gradient)' }}></div>
      </div>

      {/* Question Card */}
      <div className="pf-panel" style={{ padding: '24px', marginBottom: '20px' }}>
        <h3 style={{ fontFamily: 'Space Grotesk, sans-serif', fontSize: '16px', fontWeight: 700, marginBottom: '14px', color: 'var(--text-primary)' }}>
          {currentItem.prompt}
        </h3>

        {currentItem.code_snippet && (
          <pre
            style={{
              background: 'var(--bg-paper)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '8px',
              padding: '14px',
              fontFamily: 'IBM Plex Mono, monospace',
              fontSize: '12px',
              color: 'var(--text-primary)',
              overflowX: 'auto',
              marginBottom: '16px',
            }}
          >
            <code>{currentItem.code_snippet}</code>
          </pre>
        )}

        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {currentItem.options.map((opt, idx) => {
            const isSelected = answers[currentItem.item_id] === opt;
            const letter = String.fromCharCode(65 + idx);
            return (
              <div
                key={idx}
                onClick={() => handleSelectOption(currentItem.item_id, opt)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  padding: '12px 16px',
                  borderRadius: '8px',
                  background: isSelected ? 'var(--c-coral-tint)' : 'var(--bg-paper)',
                  border: `2px solid ${isSelected ? 'var(--c-coral)' : 'var(--border-subtle)'}`,
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                }}
              >
                <div
                  style={{
                    width: '26px',
                    height: '26px',
                    borderRadius: '50%',
                    background: isSelected ? 'var(--c-coral)' : 'var(--bg-card)',
                    color: isSelected ? '#FFFFFF' : 'var(--text-primary)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontWeight: 700,
                    fontSize: '12px',
                  }}
                >
                  {letter}
                </div>
                <span style={{ fontSize: '13px', color: 'var(--text-primary)' }}>{opt}</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Navigation Buttons */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <button
          className="btn btn-secondary"
          disabled={currentIndex === 0}
          onClick={() => setCurrentIndex((prev) => Math.max(0, prev - 1))}
        >
          ◀ Previous
        </button>

        <div style={{ display: 'flex', gap: '10px' }}>
          {currentIndex < items.length - 1 ? (
            <button
              className="btn btn-primary"
              onClick={() => setCurrentIndex((prev) => Math.min(items.length - 1, prev + 1))}
            >
              Next Question ▶
            </button>
          ) : (
            <button className="btn btn-primary" onClick={handleSubmit} disabled={submitting}>
              {submitting ? 'Calibrating Intelligence...' : 'Submit & Analyze Gaps ➔'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
