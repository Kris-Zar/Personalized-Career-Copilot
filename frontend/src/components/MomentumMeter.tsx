import React from 'react';

interface Props {
  streakDays?: number;
  xp?: number;
}

export const MomentumMeter: React.FC<Props> = ({ streakDays = 3, xp = 1250 }) => {
  return (
    <div className="momentum-meter" title={`${streakDays}-Day Learning Streak · ${xp} XP`}>
      <span>🔥</span>
      <span>{streakDays}d Streak</span>
      <div className="momentum-bar">
        <div className="momentum-fill" style={{ width: '75%' }}></div>
      </div>
      <span style={{ color: 'var(--c-coral)', fontWeight: 700 }}>{xp} XP</span>
    </div>
  );
};
