import React from 'react';
import { Link } from 'react-router-dom';

const CARDS = [
  { to: '/hotel',      emoji: '🏨', label: 'Hotel Dashboard',      accent: 'var(--accent-hotel)',       desc: 'Occupancy, ADR, RevPAR, 14-day ML forecast, channel breakdown.' },
  { to: '/restaurant', emoji: '🍽️', label: 'Restaurant Dashboard',  accent: 'var(--accent-restaurant)',  desc: 'Daily sales by service type, top products, monthly revenue trend.' },
  { to: '/realestate', emoji: '🏗️', label: 'Real Estate Dashboard', accent: 'var(--accent-realestate)', desc: 'Lead conversion funnel, unit inventory status, AI lead scoring.' },
];

export default function Overview() {
  return (
    <div>
      <h1 style={{ fontSize: '1.6rem', fontWeight: 700, marginBottom: '.4rem' }}>OneView Platform</h1>
      <p style={{ color: 'var(--text-muted)', marginBottom: '2rem', maxWidth: 560 }}>
        Unified analytics and AI-powered forecasting for hotel, restaurant, and real estate operations.
      </p>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem' }}>
        {CARDS.map(c => (
          <Link key={c.to} to={c.to}>
            <div className="card" style={{
              borderTop: `3px solid ${c.accent}`, cursor: 'pointer',
              transition: 'transform .15s, box-shadow .15s'
            }}
              onMouseEnter={e => e.currentTarget.style.transform = 'translateY(-3px)'}
              onMouseLeave={e => e.currentTarget.style.transform = 'translateY(0)'}
            >
              <div style={{ fontSize: '2rem', marginBottom: '.6rem' }}>{c.emoji}</div>
              <div style={{ fontWeight: 600, fontSize: '1rem', marginBottom: '.4rem' }}>{c.label}</div>
              <div style={{ fontSize: '.82rem', color: 'var(--text-muted)', lineHeight: 1.5 }}>{c.desc}</div>
            </div>
          </Link>
        ))}
      </div>
      <div className="card" style={{ marginTop: '1.5rem' }}>
        <div className="section-title">Quick Links</div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '.75rem', fontSize: '.85rem' }}>
          {[
            ['API Gateway Docs', 'http://localhost:8000/docs'],
            ['AI Chatbot UI', 'http://localhost:8005/chat'],
            ['Hotel Service', 'http://localhost:8001/docs'],
            ['Restaurant Service', 'http://localhost:8002/docs'],
            ['Real Estate Service', 'http://localhost:8003/docs'],
            ['Analytics Service', 'http://localhost:8004/docs'],
          ].map(([label, href]) => (
            <a key={href} href={href} target="_blank" style={{
              padding: '.35rem .8rem', borderRadius: 6,
              background: 'var(--surface-2)', border: '1px solid var(--border)',
              color: 'var(--primary-light)'
            }}>{label}</a>
          ))}
        </div>
      </div>
    </div>
  );
}
