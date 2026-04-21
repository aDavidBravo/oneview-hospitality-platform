# Restaurant Service

FastAPI microservice for the **Fine Dining Restaurant domain**.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/restaurant/kpis/daily-sales?date=YYYY-MM-DD` | Daily sales by service |
| GET | `/restaurant/kpis/weekly-sales?start=&end=` | Weekly breakdown |
| GET | `/restaurant/kpis/by-service?start=&end=` | Aggregated by service type |
| GET | `/restaurant/kpis/monthly?year=&month=` | Monthly totals |
| GET | `/restaurant/kpis/day-of-week?start=&end=` | Sales pattern by weekday |
| GET | `/restaurant/products/top?period=last_30_days` | Top selling items |
| GET | `/restaurant/products/margin-by-category?start=&end=` | Margin by category |
| GET | `/restaurant/products/inventory` | Inventory levels |

## Quick Test

```bash
curl "http://localhost:8002/restaurant/kpis/daily-sales?date=2024-06-15"
curl "http://localhost:8002/restaurant/products/top?period=last_90_days"
curl "http://localhost:8002/restaurant/kpis/by-service?start=2024-01-01&end=2024-12-31"
```

## Interactive Docs

http://localhost:8002/docs
