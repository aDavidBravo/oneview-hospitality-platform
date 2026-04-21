# Hotel Service

FastAPI microservice for the **Hotel 5★ domain**.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Service health check |
| GET | `/hotel/kpis/daily?date=YYYY-MM-DD` | Daily KPIs (occupancy, ADR, RevPAR) |
| GET | `/hotel/kpis/monthly?year=2024&month=1` | Monthly KPI aggregation |
| GET | `/hotel/kpis/summary?start=&end=` | Summary for date range |
| GET | `/hotel/kpis/trend?start=&end=` | Daily trend series |
| GET | `/hotel/reservations/?start=&end=` | List reservations with filters |
| GET | `/hotel/reservations/by-channel?start=&end=` | Revenue by booking channel |
| GET | `/hotel/reservations/by-country?start=&end=` | Reservations by guest country |
| GET | `/hotel/rooms/` | All rooms with stats |
| GET | `/hotel/rooms/availability?checkin=&checkout=` | Available rooms for dates |

## Quick Test

```bash
# Daily KPIs
curl http://localhost:8001/hotel/kpis/daily?date=2024-06-15

# Monthly summary
curl "http://localhost:8001/hotel/kpis/monthly?year=2024&month=6"

# Reservations in January 2024
curl "http://localhost:8001/hotel/reservations/?start=2024-01-01&end=2024-01-31"

# Revenue by channel
curl "http://localhost:8001/hotel/reservations/by-channel?start=2024-01-01&end=2024-12-31"
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://...@postgres:5432/oneview` | PostgreSQL connection |
| `SERVICE_NAME` | `hotel-service` | Service identifier |

## Interactive Docs

http://localhost:8001/docs
