# 🏗️ Real Estate Service

FastAPI microservice for residential/office unit inventory, lead pipeline, and contract revenue.
Runs on **port 8003** · Interactive docs: `http://localhost:8003/docs`

---

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/realestate/kpis/funnel` | Lead funnel stages & conversion rates |
| GET | `/realestate/kpis/by-source` | Lead volume & conversion by acquisition channel |
| GET | `/realestate/kpis/revenue` | Contract revenue summary |
| GET | `/realestate/kpis/units-status` | Unit inventory by status and project |
| GET | `/realestate/projects` | Project catalog with details |

---

## Quick Start (curl)

### 1. Token
```bash
TOKEN=$(curl -s -X POST http://localhost:8000/auth/token \
  -d "username=analyst&password=analyst2024" \
  -H "Content-Type: application/x-www-form-urlencoded" | jq -r .access_token)
```

### 2. Lead funnel
```bash
curl -s http://localhost:8000/realestate/kpis/funnel \
  -H "Authorization: Bearer $TOKEN" | jq
```
Sample response:
```json
{
  "overall_conversion_rate": 18.4,
  "funnel_stages": [
    { "stage": "new",        "count": 640 },
    { "stage": "contacted",  "count": 498 },
    { "stage": "visit",      "count": 312 },
    { "stage": "negotiation","count": 156 },
    { "stage": "signed",     "count": 118 }
  ]
}
```

### 3. Unit inventory
```bash
curl -s http://localhost:8000/realestate/kpis/units-status \
  -H "Authorization: Bearer $TOKEN" | jq
```

### 4. Contract revenue
```bash
curl -s http://localhost:8000/realestate/kpis/revenue \
  -H "Authorization: Bearer $TOKEN" | jq
```

### 5. Projects
```bash
curl -s http://localhost:8000/realestate/projects \
  -H "Authorization: Bearer $TOKEN" | jq '.projects'
```

### 6. Leads by acquisition source
```bash
curl -s http://localhost:8000/realestate/kpis/by-source \
  -H "Authorization: Bearer $TOKEN" | jq '.sources'
```
