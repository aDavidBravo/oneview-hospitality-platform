import React from 'react';

export default function KpiCard({ label, value, sub, accent, delta }) {
  const up = delta >= 0;
  return (
    <div className="card" style={{ borderTop: `3px solid ${accent || 'var(--primary)'}` }}>
      <div style={{ fontSize: '.75rem', color: 'var(--text-muted)', marginBottom: '.3rem' }}>{label}</div>
      <div style={{ fontSize: '1.6rem', fontWeight: 700, color: '#fff', lineHeight: 1.1 }}>{value ?? '—'}</div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '.5rem', marginTop: '.3rem' }}>
        {sub && <span style={{ fontSize: '.75rem', color: 'var(--text-muted)' }}>{sub}</span>}
        {delta != null && (
          <span className={`badge ${up ? 'up' : 'down'}`}>
            {up ? '▲' : '▼'} {Math.abs(delta)}%
          </span>
        )}
      </div>
    </div>
  );
}
