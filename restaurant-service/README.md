# 🍽️ Restaurant Service

FastAPI microservice for restaurant sales analytics, menu items, and revenue trends.
Runs on **port 8002** · Interactive docs: `http://localhost:8002/docs`

---

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/restaurant/kpis/summary` | 24-month revenue summary |
| GET | `/restaurant/kpis/daily-sales` | Daily sales by service type |
| GET | `/restaurant/kpis/monthly-sales` | Monthly revenue stacked by service |
| GET | `/restaurant/kpis/trend` | Rolling daily trend (last N days) |
| GET | `/restaurant/kpis/top-products` | Top items by revenue |
| GET | `/restaurant/menu` | Full menu with prices & categories |

---

## Quick Start (curl)

### 1. Token (via gateway)
```bash
TOKEN=$(curl -s -X POST http://localhost:8000/auth/token \
  -d "username=analyst&password=analyst2024" \
  -H "Content-Type: application/x-www-form-urlencoded" | jq -r .access_token)
```

### 2. Revenue summary
```bash
curl -s http://localhost:8000/restaurant/kpis/summary \
  -H "Authorization: Bearer $TOKEN" | jq
```
Sample response:
```json
{
  "total_revenue": 3142800,
  "total_tickets": 48260,
  "avg_ticket_value": 65.12,
  "best_month": "2024-12",
  "best_month_revenue": 298450
}
```

### 3. Monthly sales by service type
```bash
curl -s http://localhost:8000/restaurant/kpis/monthly-sales \
  -H "Authorization: Bearer $TOKEN" | jq '.monthly_data[:2]'
```

### 4. Top 10 products
```bash
curl -s "http://localhost:8000/restaurant/kpis/top-products?limit=10" \
  -H "Authorization: Bearer $TOKEN" | jq '.top_products'
```

### 5. Daily trend (last 30 days)
```bash
curl -s "http://localhost:8000/restaurant/kpis/trend?days=30" \
  -H "Authorization: Bearer $TOKEN" | jq '.daily_trend[-5:]'
```

### 6. Full menu
```bash
curl -s http://localhost:8000/restaurant/menu \
  -H "Authorization: Bearer $TOKEN" | jq '.items[:5]'
```
