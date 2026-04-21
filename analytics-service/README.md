# 🧠 Analytics Service

FastAPI microservice with 3 scikit-learn ML models for forecasting and lead scoring.
Runs on **port 8004** · Interactive docs: `http://localhost:8004/docs`

---

## Models

| Model | Algorithm | Target | MAE |
|-------|-----------|--------|-----|
| Hotel Occupancy | GradientBoostingRegressor | Daily occupancy rate | ~3.8% |
| Restaurant Sales | RandomForestRegressor (per service) | Daily revenue | ~$380 |
| RE Lead Conversion | GradientBoostingClassifier | Conversion probability | ROC-AUC ~0.83 |

---

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/analytics/train/hotel-occupancy` | Train hotel forecast model |
| POST | `/analytics/predict/hotel-occupancy` | Predict next N days occupancy |
| POST | `/analytics/train/restaurant-sales` | Train restaurant models |
| POST | `/analytics/predict/restaurant-sales` | Forecast revenue by service type |
| POST | `/analytics/train/realestate-conversion` | Train lead classifier |
| POST | `/analytics/predict/realestate-conversion` | Score a single lead |
| GET | `/analytics/predict/realestate-leads-bulk` | Score all active leads |
| POST | `/analytics/train-all` | Retrain all 3 models at once |

---

## Quick Start (curl)

### 1. Token
```bash
TOKEN=$(curl -s -X POST http://localhost:8000/auth/token \
  -d "username=admin&password=oneview2024" \
  -H "Content-Type: application/x-www-form-urlencoded" | jq -r .access_token)
```

### 2. Train all models (first-time setup)
```bash
curl -s -X POST http://localhost:8000/analytics/train-all \
  -H "Authorization: Bearer $TOKEN" | jq
```

### 3. Hotel occupancy forecast (14 days)
```bash
curl -s -X POST http://localhost:8000/analytics/predict/hotel-occupancy \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"days_ahead": 14}' | jq '.predictions[:3]'
```
Sample response:
```json
[
  { "date": "2025-01-01", "predicted_occupancy": 0.821 },
  { "date": "2025-01-02", "predicted_occupancy": 0.795 },
  { "date": "2025-01-03", "predicted_occupancy": 0.773 }
]
```

### 4. Restaurant forecast (next 7 days)
```bash
curl -s -X POST http://localhost:8000/analytics/predict/restaurant-sales \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"days_ahead": 7}' | jq
```

### 5. Score a real estate lead
```bash
curl -s -X POST http://localhost:8000/analytics/predict/realestate-conversion \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "lead_id": 42,
    "source": "referral",
    "project_id": 1,
    "interested_unit_type": "apartment",
    "interaction_count": 5,
    "days_since_created": 30,
    "days_since_contact": 3,
    "budget_usd": 120000
  }' | jq
```

### 6. Bulk lead scoring
```bash
curl -s http://localhost:8000/analytics/predict/realestate-leads-bulk \
  -H "Authorization: Bearer $TOKEN" | jq '.leads[:5]'
```
