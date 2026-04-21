# 🏨 Hotel Service

FastAPI microservice for hotel KPIs, reservations, and room availability.
Runs on **port 8001** · Interactive docs: `http://localhost:8001/docs`

---

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/hotel/kpis/summary` | 24-month aggregate (occupancy, ADR, RevPAR, revenue) |
| GET | `/hotel/kpis/daily` | KPIs per day (optional `?start=` / `?end=` filters) |
| GET | `/hotel/kpis/range` | KPIs for a custom date range |
| GET | `/hotel/kpis/monthly` | Monthly rollup |
| GET | `/hotel/kpis/by-channel` | Booking volume & revenue by sales channel |
| GET | `/hotel/reservations` | Paginated reservations list |
| GET | `/hotel/reservations/by-country` | Guest origin breakdown |
| GET | `/hotel/rooms` | All rooms with type & status |
| GET | `/hotel/rooms/availability` | Availability for a date window |

---

## Quick Start (curl)

### 1. Get a JWT token from the gateway
```bash
curl -s -X POST http://localhost:8000/auth/token \
  -d "username=analyst&password=analyst2024" \
  -H "Content-Type: application/x-www-form-urlencoded" | jq .access_token
```
Set the token:
```bash
TOKEN="<paste token here>"
```

### 2. 24-month summary
```bash
curl -s http://localhost:8000/hotel/kpis/summary \
  -H "Authorization: Bearer $TOKEN" | jq
```
Sample response:
```json
{
  "avg_occupancy_rate": 0.742,
  "avg_adr": 187.35,
  "avg_revpar": 139.02,
  "total_revenue": 4218760,
  "total_reservations": 15340
}
```

### 3. Monthly KPIs
```bash
curl -s http://localhost:8000/hotel/kpis/monthly \
  -H "Authorization: Bearer $TOKEN" | jq '.monthly_data[:3]'
```

### 4. Channel breakdown
```bash
curl -s http://localhost:8000/hotel/kpis/by-channel \
  -H "Authorization: Bearer $TOKEN" | jq '.channels'
```

### 5. Room availability (next 7 days)
```bash
curl -s "http://localhost:8000/hotel/rooms/availability?start_date=2025-01-01&end_date=2025-01-07" \
  -H "Authorization: Bearer $TOKEN" | jq
```

### 6. Reservations by guest country
```bash
curl -s http://localhost:8000/hotel/reservations/by-country \
  -H "Authorization: Bearer $TOKEN" | jq '.countries[:5]'
```
