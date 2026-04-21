import axios from 'axios';

const BASE = import.meta.env.VITE_GATEWAY_URL || 'http://localhost:8000';

const api = axios.create({ baseURL: BASE });

// Token store (demo: auto-login)
let _token = null;

export async function getToken() {
  if (_token) return _token;
  const form = new URLSearchParams();
  form.append('username', 'analyst');
  form.append('password', 'analyst2024');
  const { data } = await api.post('/auth/token', form, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
  });
  _token = data.access_token;
  return _token;
}

async function auth() {
  const t = await getToken();
  return { headers: { Authorization: `Bearer ${t}` } };
}

// Hotel
export async function fetchHotelSummary()     { return api.get('/hotel/kpis/summary',      await auth()); }
export async function fetchHotelMonthly()     { return api.get('/hotel/kpis/monthly',      await auth()); }
export async function fetchHotelChannels()    { return api.get('/hotel/kpis/by-channel',   await auth()); }
export async function fetchHotelForecast()    {
  return api.post('/analytics/predict/hotel-occupancy', { days_ahead: 14 }, await auth());
}

// Restaurant
export async function fetchRestSummary()      { return api.get('/restaurant/kpis/summary',      await auth()); }
export async function fetchRestMonthly()      { return api.get('/restaurant/kpis/monthly-sales', await auth()); }
export async function fetchRestTopProducts()  { return api.get('/restaurant/kpis/top-products',  await auth()); }
export async function fetchRestTrend()        { return api.get('/restaurant/kpis/trend',          await auth()); }

// Real Estate
export async function fetchREFunnel()         { return api.get('/realestate/kpis/funnel',       await auth()); }
export async function fetchREUnits()          { return api.get('/realestate/kpis/units-status', await auth()); }
export async function fetchRERevenue()        { return api.get('/realestate/kpis/revenue',       await auth()); }
export async function fetchRELeads()          { return api.get('/analytics/predict/realestate-leads-bulk', await auth()); }
