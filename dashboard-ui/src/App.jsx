import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import HotelDashboard from './pages/HotelDashboard.jsx';
import RestaurantDashboard from './pages/RestaurantDashboard.jsx';
import RealEstateDashboard from './pages/RealEstateDashboard.jsx';
import Overview from './pages/Overview.jsx';

const NAV = [
  { to: '/',           label: '🏠 Overview',    exact: true },
  { to: '/hotel',      label: '🏨 Hotel' },
  { to: '/restaurant', label: '🍽️ Restaurant' },
  { to: '/realestate', label: '🏗️ Real Estate' },
];

export default function App() {
  return (
    <BrowserRouter>
      <div style={{ display: 'flex', minHeight: '100vh' }}>
        {/* Sidebar */}
        <aside style={{
          width: 220, background: '#161926', borderRight: '1px solid var(--border)',
          display: 'flex', flexDirection: 'column', padding: '1.5rem 1rem', gap: '.5rem', flexShrink: 0
        }}>
          <div style={{ marginBottom: '1.5rem' }}>
            <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#fff' }}>OneView</div>
            <div style={{ fontSize: '.72rem', color: 'var(--text-muted)' }}>Hospitality Platform</div>
          </div>
          {NAV.map(n => (
            <NavLink key={n.to} to={n.to} end={!!n.exact} style={({ isActive }) => ({
              padding: '.55rem .85rem', borderRadius: 8,
              background: isActive ? 'rgba(99,102,241,.18)' : 'transparent',
              color: isActive ? 'var(--primary-light)' : 'var(--text-muted)',
              fontWeight: isActive ? 600 : 400, fontSize: '.88rem',
              transition: 'all .15s'
            })}>
              {n.label}
            </NavLink>
          ))}
          <div style={{ marginTop: 'auto', fontSize: '.72rem', color: 'var(--text-muted)', lineHeight: 1.6 }}>
            <div>Gateway: <a href="http://localhost:8000/docs" target="_blank" style={{ color: 'var(--primary-light)' }}>API Docs</a></div>
            <div>Chatbot: <a href="http://localhost:8005/chat" target="_blank" style={{ color: 'var(--primary-light)' }}>Open UI</a></div>
          </div>
        </aside>

        {/* Main */}
        <main style={{ flex: 1, padding: '2rem', overflowY: 'auto' }}>
          <Routes>
            <Route path="/"           element={<Overview />} />
            <Route path="/hotel"      element={<HotelDashboard />} />
            <Route path="/restaurant" element={<RestaurantDashboard />} />
            <Route path="/realestate" element={<RealEstateDashboard />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
