"""
Analytics Service - Restaurant Sales Forecasting
Random Forest Regressor per service type
"""
import os
import joblib
import numpy as np
import pandas as pd
from datetime import date, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error
import logging

from ..database import get_db, MODEL_PATH

logger = logging.getLogger(__name__)
router = APIRouter()

MODEL_FILE = os.path.join(MODEL_PATH, 'restaurant_sales_model.pkl')
_models = {}  # one model per service_type


def get_features(d: date) -> list:
    return [
        d.weekday(),
        d.month,
        (d.month - 1) // 3 + 1,
        d.timetuple().tm_yday,
        1 if d.weekday() >= 5 else 0,
        1 if d.month in (12, 1, 2, 7, 8) else 0,
        1 if d.month == 2 and 5 <= d.day <= 20 else 0,
    ]


async def train_restaurant_model():
    global _models
    
    DATABASE_URL = os.getenv('DATABASE_URL')
    from sqlalchemy import create_engine
    engine = create_engine(DATABASE_URL)
    
    df = pd.read_sql("""
        SELECT sale_date, service_type, total_revenue
        FROM restaurant.daily_sales_summary
        ORDER BY sale_date, service_type
    """, engine)
    
    if len(df) < 30:
        return {"error": "Insufficient data"}
    
    df['sale_date'] = pd.to_datetime(df['sale_date'])
    metrics = {}
    
    for svc in df['service_type'].unique():
        svc_df = df[df['service_type'] == svc].copy()
        svc_df = svc_df.sort_values('sale_date')
        
        # Lag features
        svc_df['lag_7'] = svc_df['total_revenue'].shift(7).fillna(svc_df['total_revenue'].mean())
        svc_df['lag_14'] = svc_df['total_revenue'].shift(14).fillna(svc_df['total_revenue'].mean())
        svc_df['rolling_7'] = svc_df['total_revenue'].rolling(7, min_periods=1).mean()
        
        feats = svc_df.apply(lambda r: get_features(r['sale_date'].date()), axis=1, result_type='expand')
        feats.columns = ['dow', 'month', 'quarter', 'doy', 'is_weekend', 'is_high_season', 'is_carnival']
        X = pd.concat([feats, svc_df[['lag_7', 'lag_14', 'rolling_7']].reset_index(drop=True)], axis=1).values
        y = svc_df['total_revenue'].values
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
        
        model = RandomForestRegressor(n_estimators=150, max_depth=6, random_state=42, n_jobs=-1)
        model.fit(X_train, y_train)
        
        y_pred = model.predict(X_test)
        mae = float(mean_absolute_error(y_test, y_pred))
        rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
        
        _models[svc] = {'model': model, 'last_values': list(svc_df['total_revenue'].tail(30))}
        metrics[svc] = {'mae': mae, 'rmse': rmse, 'samples': len(svc_df)}
    
    joblib.dump(_models, MODEL_FILE)
    logger.info(f"Restaurant models trained for: {list(_models.keys())}")
    
    return {"status": "trained", "metrics": metrics}


@router.post("/train/restaurant-sales", summary="Train restaurant sales forecast model")
async def trigger_training():
    return await train_restaurant_model()


@router.post("/predict/restaurant-sales", summary="Predict restaurant sales next 14 days")
async def predict_restaurant_sales(
    horizon_days: int = 14,
    db: Session = Depends(get_db)
):
    global _models
    
    if not _models and os.path.exists(MODEL_FILE):
        _models = joblib.load(MODEL_FILE)
    
    today = date.today()
    predictions = []
    
    service_types = ['breakfast', 'lunch', 'dinner', 'bar', 'room_service']
    base_revenues = {'breakfast': 800, 'lunch': 1200, 'dinner': 2500, 'bar': 600, 'room_service': 400}
    
    for i in range(1, horizon_days + 1):
        d = today + timedelta(days=i)
        day_prediction = {"date": str(d), "day_of_week": d.strftime('%A'), "by_service": []}
        total_day = 0
        
        for svc in service_types:
            if svc in _models:
                features = get_features(d)
                last_vals = _models[svc]['last_values']
                lag_7 = last_vals[-7] if len(last_vals) >= 7 else np.mean(last_vals)
                lag_14 = last_vals[-14] if len(last_vals) >= 14 else np.mean(last_vals)
                rolling_7 = np.mean(last_vals[-7:]) if len(last_vals) >= 7 else np.mean(last_vals)
                X = np.array([features + [lag_7, lag_14, rolling_7]])
                pred = float(_models[svc]['model'].predict(X)[0])
            else:
                # Heuristic fallback
                base = base_revenues.get(svc, 500)
                if d.weekday() >= 5:
                    base *= 1.3
                if d.month in (12, 1, 2):
                    base *= 1.2
                pred = base * np.random.uniform(0.85, 1.15)
            
            pred = max(0, pred)
            day_prediction["by_service"].append({
                "service_type": svc,
                "predicted_revenue": round(pred, 2)
            })
            total_day += pred
        
        day_prediction["total_predicted_revenue"] = round(total_day, 2)
        predictions.append(day_prediction)
    
    return {
        "model": "RandomForestRegressor" if _models else "heuristic_fallback",
        "horizon_days": horizon_days,
        "predictions": predictions
    }
