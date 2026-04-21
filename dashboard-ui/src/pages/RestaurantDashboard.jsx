import React, { useEffect, useState } from 'react';
import {
  BarChart, Bar, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell
} from 'recharts';
import KpiCard from '../components/KpiCard.jsx';
import Loader from '../components/Loader.jsx';
import { fetchRestSummary, fetchRestMonthly, fetchRestTopProducts, fetchRestTrend } from '../api.js';

const SERVICE_COLORS = { breakfast: '#f59e0b', lunch: '#38bdf8', dinner: '#818cf8', bar: '#f43f5e', room_service: '#10b981' };
const TOP_COLORS = ['#818cf8','#38bdf8','#f59e0b','#10b981','#f43f5e','#a78bfa','#34d399','#fbbf24'];

function usd(v) { return v != null ? `$${Number(v).toLocaleString('en-US', { maximumFractionDigits: 0 })}` : '—'; }

export default function RestaurantDashboard() {
  const [summary, setSummary]   = useState(null);
  const [monthly, setMonthly]   = useState(null);
  const [products, setProducts] = useState(null);
  const [trend, setTrend]       = useState(null);
  const [loading, setLoading]   = useState(true);

  useEffect(() => {
    Promise.all([
      fetchRestSummary(),
      fetchRestMonthly(),
      fetchRestTopProducts(),
      fetchRestTrend()
    ]).then(([s, m, p, t]) => {
      setSummary(s.data);
      setMonthly(m.data);
      setProducts(p.data);
      setTrend(t.data);
    }).finally(() => setLoading(false));
  }, []);

  if (loading) return <Loader />;

  const monthlyData = monthly?.monthly_data || [];
  const topProducts = products?.top_products?.slice(0, 8) || [];
  const trendData   = trend?.daily_trend?.slice(-60) || [];

  return (
    <div>
      <h2 style={{ fontWeight: 700, fontSize: '1.3rem', marginBottom: '1.25rem' }}>🍽️ Restaurant Dashboard</h2>

      <div className="kpi-grid">
        <KpiCard label="Total Revenue (2yr)"   value={usd(summary?.total_revenue)}        accent="#f59e0b" />
        <KpiCard label="Total Tickets"         value={summary?.total_tickets?.toLocaleString()} accent="#38bdf8" sub="All service types" />
        <KpiCard label="Avg Ticket Value"      value={usd(summary?.avg_ticket_value)}      accent="#818cf8" sub="Per transaction" />
        <KpiCard label="Best Month Revenue"    value={usd(summary?.best_month_revenue)}    accent="#10b981" sub={summary?.best_month} />
      </div>

      <div className="chart-grid">
        <div className="card">
          <div className="section-title">Monthly Revenue by Service Type</div>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={monthlyData} margin={{ top: 5, right: 10, bottom: 5, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2d3148" />
              <XAxis dataKey="month" tick={{ fontSize: 9, fill: '#94a3b8' }} />
              <YAxis tickFormatter={v => `$${(v/1000).toFixed(0)}k`} tick={{ fontSize: 10, fill: '#94a3b8' }} />
              <Tooltip formatter={v => `$${Number(v).toLocaleString()}`} contentStyle={{ background: '#1e2130', border: '1px solid #2d3148', borderRadius: 8 }} />
              <Legend />
              {Object.entries(SERVICE_COLORS).map(([k, c]) => (
                <Bar key={k} dataKey={k} name={k.replace('_', ' ')} stackId="a" fill={c} />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <div className="section-title">Top 8 Products by Revenue</div>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={topProducts} layout="vertical" margin={{ top: 5, right: 20, bottom: 5, left: 80 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2d3148" horizontal={false} />
              <XAxis type="number" tickFormatter={v => `$${(v/1000).toFixed(0)}k`} tick={{ fontSize: 10, fill: '#94a3b8' }} />
              <YAxis dataKey="item_name" type="category" tick={{ fontSize: 9, fill: '#94a3b8' }} width={80} />
              <Tooltip formatter={v => `$${Number(v).toLocaleString()}`} contentStyle={{ background: '#1e2130', border: '1px solid #2d3148', borderRadius: 8 }} />
              <Bar dataKey="total_revenue" name="Revenue" radius={[0, 4, 4, 0]}>
                {topProducts.map((_, i) => <Cell key={i} fill={TOP_COLORS[i % TOP_COLORS.length]} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="card">
        <div className="section-title">Daily Revenue Trend (Last 60 Days)</div>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={trendData} margin={{ top: 5, right: 10, bottom: 5, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#2d3148" />
            <XAxis dataKey="date" tick={{ fontSize: 9, fill: '#94a3b8' }} interval={9} />
            <YAxis tickFormatter={v => `$${(v/1000).toFixed(0)}k`} tick={{ fontSize: 10, fill: '#94a3b8' }} />
            <Tooltip formatter={v => `$${Number(v).toLocaleString()}`} contentStyle={{ background: '#1e2130', border: '1px solid #2d3148', borderRadius: 8 }} />
            <Line type="monotone" dataKey="total_revenue" name="Revenue" stroke="#f59e0b" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
