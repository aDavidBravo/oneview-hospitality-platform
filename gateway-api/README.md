# 🔑 Gateway API

Central entry point for the OneView platform. Handles JWT authentication and reverse-proxies to all downstream microservices.
Runs on **port 8000** · Interactive docs: `http://localhost:8000/docs`

---

## Demo Users

| Username | Password | Role |
|----------|----------|------|
| `admin` | `oneview2024` | Full access |
| `director` | `director2024` | Read + train models |
| `analyst` | `analyst2024` | Read-only dashboards |

---

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/token` | Obtain JWT (OAuth2 password flow) |
| GET | `/health` | Platform-wide health check |
| ANY | `/hotel/*` | Proxy → hotel-service:8001 |
| ANY | `/restaurant/*` | Proxy → restaurant-service:8002 |
| ANY | `/realestate/*` | Proxy → realestate-service:8003 |
| ANY | `/analytics/*` | Proxy → analytics-service:8004 |
| ANY | `/chatbot/*` | Proxy → chatbot-service:8005 |

---

## Quick Start (curl)

### 1. Authenticate
```bash
curl -s -X POST http://localhost:8000/auth/token \
  -d "username=admin&password=oneview2024" \
  -H "Content-Type: application/x-www-form-urlencoded"
```
Response:
```json
{ "access_token": "eyJ...", "token_type": "bearer" }
```

### 2. Health check
```bash
curl -s http://localhost:8000/health | jq
```
Response:
```json
{
  "status": "healthy",
  "services": {
    "hotel": "ok", "restaurant": "ok",
    "realestate": "ok", "analytics": "ok", "chatbot": "ok"
  }
}
```

### 3. One-liner: token + hotel summary
```bash
TOKEN=$(curl -s -X POST http://localhost:8000/auth/token \
  -d "username=analyst&password=analyst2024" \
  -H "Content-Type: application/x-www-form-urlencoded" | jq -r .access_token)

curl -s http://localhost:8000/hotel/kpis/summary \
  -H "Authorization: Bearer $TOKEN" | jq
```

### 4. Train all ML models (admin only)
```bash
TOKEN=$(curl -s -X POST http://localhost:8000/auth/token \
  -d "username=admin&password=oneview2024" \
  -H "Content-Type: application/x-www-form-urlencoded" | jq -r .access_token)

curl -s -X POST http://localhost:8000/analytics/train-all \
  -H "Authorization: Bearer $TOKEN" | jq
```
