import React, { useEffect, useState } from 'react';
import {
  BarChart, Bar, FunnelChart, Funnel, LabelList,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, PieChart, Pie, Legend
} from 'recharts';
import KpiCard from '../components/KpiCard.jsx';
import Loader from '../components/Loader.jsx';
import { fetchREFunnel, fetchREUnits, fetchRERevenue, fetchRELeads } from '../api.js';

const UNIT_COLORS = { available: '#10b981', reserved: '#f59e0b', sold: '#38bdf8', unavailable: '#ef4444' };
const FUNNEL_COLORS = ['#818cf8','#38bdf8','#10b981','#f59e0b','#f43f5e'];

function usd(v) { return v != null ? `$${Number(v).toLocaleString('en-US', { maximumFractionDigits: 0 })}` : '—'; }
function pct(v) { return v != null ? `${Number(v).toFixed(1)}%` : '—'; }

export default function RealEstateDashboard() {
  const [funnel, setFunnel]   = useState(null);
  const [units, setUnits]     = useState(null);
  const [revenue, setRevenue] = useState(null);
  const [leads, setLeads]     = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetchREFunnel(),
      fetchREUnits(),
      fetchRERevenue(),
      fetchRELeads().catch(() => null)
    ]).then(([f, u, r, l]) => {
      setFunnel(f.data);
      setUnits(u.data);
      setRevenue(r.data);
      if (l) setLeads(l.data);
    }).finally(() => setLoading(false));
  }, []);

  if (loading) return <Loader />;

  const funnelStages = funnel?.funnel_stages || [];
  const unitsByProject = units?.by_project || [];
  const unitPieData = Object.entries(units?.overall || {}).map(([k, v]) => ({ name: k, value: v }));
  const leadsData = leads?.leads?.slice(0, 10) || [];

  return (
    <div>
      <h2 style={{ fontWeight: 700, fontSize: '1.3rem', marginBottom: '1.25rem' }}>🏗️ Real Estate Dashboard</h2>

      <div className="kpi-grid">
        <KpiCard label="Total Contract Revenue" value={usd(revenue?.total_contract_value)}  accent="#10b981" />
        <KpiCard label="Units Sold"              value={units?.overall?.sold}               accent="#38bdf8" />
        <KpiCard label="Units Available"         value={units?.overall?.available}          accent="#818cf8" />
        <KpiCard label="Funnel Conversion"        value={pct(funnel?.overall_conversion_rate)} accent="#f59e0b" sub="Lead → Contract" />
        <KpiCard label="Avg Contract Value"       value={usd(revenue?.avg_contract_value)}   accent="#a78bfa" sub="Per signed unit" />
      </div>

      <div className="chart-grid">
        <div className="card">
          <div className="section-title">Lead Conversion Funnel</div>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={funnelStages} layout="vertical" margin={{ top: 5, right: 20, bottom: 5, left: 80 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2d3148" horizontal={false} />
              <XAxis type="number" tick={{ fontSize: 10, fill: '#94a3b8' }} />
              <YAxis dataKey="stage" type="category" tick={{ fontSize: 10, fill: '#94a3b8' }} width={80} />
              <Tooltip contentStyle={{ background: '#1e2130', border: '1px solid #2d3148', borderRadius: 8 }} />
              <Bar dataKey="count" name="Leads" radius={[0, 4, 4, 0]}>
                {funnelStages.map((_, i) => <Cell key={i} fill={FUNNEL_COLORS[i % FUNNEL_COLORS.length]} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <div className="section-title">Units by Status</div>
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie data={unitPieData} cx="50%" cy="50%" innerRadius={60} outerRadius={100} paddingAngle={3} dataKey="value" nameKey="name">
                {unitPieData.map((e, i) => <Cell key={i} fill={UNIT_COLORS[e.name] || '#94a3b8'} />)}
              </Pie>
              <Tooltip contentStyle={{ background: '#1e2130', border: '1px solid #2d3148', borderRadius: 8 }} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {leadsData.length > 0 && (
        <div className="card">
          <div className="section-title">AI Lead Scoring — Top 10 Prospects</div>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '.82rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border)' }}>
                  {['Lead ID','Project','Source','Status','Conversion %'].map(h => (
                    <th key={h} style={{ padding: '.5rem .75rem', textAlign: 'left', color: 'var(--text-muted)', fontWeight: 500 }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {leadsData.map((l, i) => {
                  const prob = (l.conversion_probability * 100).toFixed(0);
                  const color = prob >= 70 ? '#10b981' : prob >= 40 ? '#f59e0b' : '#ef4444';
                  return (
                    <tr key={i} style={{ borderBottom: '1px solid #1e2130' }}>
                      <td style={{ padding: '.5rem .75rem' }}>{l.lead_id}</td>
                      <td style={{ padding: '.5rem .75rem' }}>{l.project_name}</td>
                      <td style={{ padding: '.5rem .75rem' }}>{l.source}</td>
                      <td style={{ padding: '.5rem .75rem' }}>{l.status}</td>
                      <td style={{ padding: '.5rem .75rem' }}>
                        <span style={{ color, fontWeight: 600 }}>{prob}%</span>
                        <div style={{ marginTop: 3, height: 4, borderRadius: 2, background: '#2d3148', overflow: 'hidden' }}>
                          <div style={{ height: '100%', width: `${prob}%`, background: color, borderRadius: 2 }} />
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
