import React, { useState } from 'react';
import { api } from '../api/client';

interface Props {
  onStateChange?: () => void;
}

export const PersonaBar: React.FC<Props> = ({ onStateChange }) => {
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  const handleLoad = async (presetId: string) => {
    setLoading(true);
    setMsg(null);
    try {
      await api.loadPreset(presetId);
      setMsg(`Loaded preset: ${presetId.toUpperCase()}`);
      if (onStateChange) onStateChange();
      window.location.reload();
    } catch (err: any) {
      setMsg(`Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = async () => {
    setLoading(true);
    try {
      await api.resetState();
      setMsg('Store reset to clean blank state.');
      if (onStateChange) onStateChange();
      window.location.reload();
    } catch (err: any) {
      setMsg(`Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="persona-bar">
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <span style={{ fontWeight: 700, color: 'var(--c-coral)' }}>⚙️ Demo Presets:</span>
        <button
          className="btn btn-secondary btn-sm"
          onClick={() => handleLoad('alex')}
          disabled={loading}
        >
          👤 Alex (Data Scientist)
        </button>
        <button
          className="btn btn-secondary btn-sm"
          onClick={() => handleLoad('kenji')}
          disabled={loading}
        >
          🔬 Kenji (ML Engineer)
        </button>
        <button
          className="btn btn-secondary btn-sm"
          onClick={() => handleLoad('aisha')}
          disabled={loading}
        >
          👩‍🏫 Aisha (Teacher Switcher)
        </button>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        {msg && <span style={{ color: 'var(--c-jade)', fontSize: '11px', fontWeight: 600 }}>{msg}</span>}
        <button
          className="btn btn-secondary btn-sm"
          onClick={handleReset}
          disabled={loading}
          style={{ borderColor: 'var(--c-coral)', color: 'var(--c-coral)' }}
        >
          🔄 Fresh Start
        </button>
      </div>
    </div>
  );
};
