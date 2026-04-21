# Analytics Service

FastAPI microservice for **AI/ML predictions** and forecasting.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/analytics/predict/hotel-occupancy` | Forecast occupancy 14 days |
| POST | `/analytics/predict/restaurant-sales` | Forecast daily sales 14 days |
| POST | `/analytics/predict/realestate-conversion` | Lead conversion probability |
| POST | `/analytics/train/all` | Retrain all models |

## Models

| Model | Algorithm | Input | Output |
|-------|-----------|-------|--------|
| Hotel Occupancy | Ridge Regression + Seasonal Features | Historical KPIs | Predicted occupancy % |
| Restaurant Sales | Ridge Regression + Lag Features | Daily sales history | Predicted revenue |
| Lead Conversion | Random Forest Classifier | Lead attributes | Probability 0-1 |

## Quick Test

```bash
# Forecast hotel occupancy
curl -X POST http://localhost:8004/analytics/predict/hotel-occupancy

# Forecast restaurant sales (30 days)
curl -X POST "http://localhost:8004/analytics/predict/restaurant-sales?horizon=30"

# Predict lead conversion
curl -X POST http://localhost:8004/analytics/predict/realestate-conversion \
  -H "Content-Type: application/json" \
  -d '{"source_channel":"referral","interest_level":"hot","unit_type_interest":"2br","interactions_count":8,"visits_count":3,"days_in_funnel":45}'

# Retrain all models
curl -X POST http://localhost:8004/analytics/train/all
```

## Interactive Docs

http://localhost:8004/docs
