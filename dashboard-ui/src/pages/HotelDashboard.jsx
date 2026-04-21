import React, { useEffect, useState } from 'react';
import {
  AreaChart, Area, BarChart, Bar, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell
} from 'recharts';
import KpiCard from '../components/KpiCard.jsx';
import Loader from '../components/Loader.jsx';
import { fetchHotelSummary, fetchHotelMonthly, fetchHotelChannels, fetchHotelForecast } from '../api.js';

const C = { occ: '#38bdf8', adr: '#818cf8', revpar: '#f59e0b', forecast: '#10b981' };
const CHANNEL_COLORS = ['#38bdf8','#818cf8','#f59e0b','#10b981','#f43f5e'];

function fmt(v, type='pct') {
  if (v == null) return '—';
  if (type === 'pct')  return `${(v * 100).toFixed(1)}%`;
  if (type === 'usd')  return `$${Number(v).toLocaleString('en-US', { maximumFractionDigits: 0 })}`;
  if (type === 'usd2') return `$${Number(v).toFixed(2)}`;
  return v;
}

export default function HotelDashboard() {
  const [summary, setSummary]   = useState(null);
  const [monthly, setMonthly]   = useState(null);
  const [channels, setChannels] = useState(null);
  const [forecast, setForecast] = useState(null);
  const [loading, setLoading]   = useState(true);

  useEffect(() => {
    Promise.all([
      fetchHotelSummary(),
      fetchHotelMonthly(),
      fetchHotelChannels(),
      fetchHotelForecast().catch(() => null)
    ]).then(([s, m, ch, f]) => {
      setSummary(s.data);
      setMonthly(m.data);
      setChannels(ch.data);
      if (f) setForecast(f.data);
    }).finally(() => setLoading(false));
  }, []);

  if (loading) return <Loader />;

  const monthlyData = monthly?.monthly_data || [];
  const channelData = channels?.channels || [];
  const forecastData = forecast?.predictions || [];

  return (
    <div>
      <h2 style={{ fontWeight: 700, fontSize: '1.3rem', marginBottom: '1.25rem' }}>🏨 Hotel Dashboard</h2>

      <div className="kpi-grid">
        <KpiCard label="Avg Occupancy (2yr)"   value={fmt(summary?.avg_occupancy_rate)}   accent={C.occ}    sub="All room types" />
        <KpiCard label="Average Daily Rate"    value={fmt(summary?.avg_adr, 'usd2')}       accent={C.adr}    sub="USD per night" />
        <KpiCard label="RevPAR"                value={fmt(summary?.avg_revpar, 'usd2')}    accent={C.revpar} sub="Revenue/available room" />
        <KpiCard label="Total Revenue"         value={fmt(summary?.total_revenue, 'usd')}  accent="#f43f5e" sub="24-month period" />
        <KpiCard label="Total Reservations"    value={summary?.total_reservations?.toLocaleString()} accent="#a78bfa" sub="Confirmed + checked-out" />
      </div>

      <div className="chart-grid">
        <div className="card">
          <div className="section-title">Monthly Occupancy & ADR</div>
          <ResponsiveContainer width="100%" height={240}>
            <AreaChart data={monthlyData} margin={{ top: 5, right: 10, bottom: 5, left: 0 }}>
              <defs>
                <linearGradient id="gOcc" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={C.occ} stopOpacity={0.3} />
                  <stop offset="95%" stopColor={C.occ} stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#2d3148" />
              <XAxis dataKey="month" tick={{ fontSize: 10, fill: '#94a3b8' }} />
              <YAxis yAxisId="occ" domain={[0, 1]} tickFormatter={v => `${(v*100).toFixed(0)}%`} tick={{ fontSize: 10, fill: '#94a3b8' }} />
              <YAxis yAxisId="adr" orientation="right" tickFormatter={v => `$${v}`} tick={{ fontSize: 10, fill: '#94a3b8' }} />
              <Tooltip formatter={(v, n) => n === 'Occupancy' ? `${(v*100).toFixed(1)}%` : `$${v.toFixed(2)}`} contentStyle={{ background: '#1e2130', border: '1px solid #2d3148', borderRadius: 8 }} />
              <Legend />
              <Area yAxisId="occ" type="monotone" dataKey="avg_occupancy_rate" name="Occupancy" stroke={C.occ} fill="url(#gOcc)" strokeWidth={2} />
              <Line yAxisId="adr" type="monotone" dataKey="avg_adr" name="ADR" stroke={C.adr} strokeWidth={2} dot={false} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <div className="section-title">Bookings by Channel</div>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={channelData} layout="vertical" margin={{ top: 5, right: 20, bottom: 5, left: 40 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2d3148" horizontal={false} />
              <XAxis type="number" tick={{ fontSize: 10, fill: '#94a3b8' }} />
              <YAxis dataKey="channel" type="category" tick={{ fontSize: 10, fill: '#94a3b8' }} />
              <Tooltip contentStyle={{ background: '#1e2130', border: '1px solid #2d3148', borderRadius: 8 }} />
              <Bar dataKey="total_bookings" name="Bookings" radius={[0, 4, 4, 0]}>
                {channelData.map((_, i) => <Cell key={i} fill={CHANNEL_COLORS[i % CHANNEL_COLORS.length]} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {forecastData.length > 0 && (
        <div className="card">
          <div className="section-title">14-Day ML Occupancy Forecast (GradientBoosting)</div>
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={forecastData} margin={{ top: 5, right: 10, bottom: 5, left: 0 }}>
              <defs>
                <linearGradient id="gFc" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={C.forecast} stopOpacity={0.3} />
                  <stop offset="95%" stopColor={C.forecast} stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#2d3148" />
              <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#94a3b8' }} />
              <YAxis domain={[0, 1]} tickFormatter={v => `${(v*100).toFixed(0)}%`} tick={{ fontSize: 10, fill: '#94a3b8' }} />
              <Tooltip formatter={v => `${(v*100).toFixed(1)}%`} contentStyle={{ background: '#1e2130', border: '1px solid #2d3148', borderRadius: 8 }} />
              <Area type="monotone" dataKey="predicted_occupancy" name="Forecast" stroke={C.forecast} fill="url(#gFc)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
