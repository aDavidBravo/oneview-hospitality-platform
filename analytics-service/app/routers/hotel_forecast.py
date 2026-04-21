"""
Analytics Service - Hotel Occupancy Forecasting
Gradient Boosting Regressor with calendar features
"""
import os
import joblib
import numpy as np
import pandas as pd
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from typing import Optional
import logging

from ..database import get_db, MODEL_PATH

logger = logging.getLogger(__name__)
router = APIRouter()

MODEL_FILE = os.path.join(MODEL_PATH, 'hotel_occupancy_model.pkl')
SCALER_FILE = os.path.join(MODEL_PATH, 'hotel_occupancy_scaler.pkl')

_model = None
_scaler = None


def get_calendar_features(d: date) -> dict:
    """Extract calendar and temporal features from a date."""
    return {
        'dayofweek': d.weekday(),
        'month': d.month,
        'quarter': (d.month - 1) // 3 + 1,
        'dayofyear': d.timetuple().tm_yday,
        'weekofyear': d.isocalendar()[1],
        'is_weekend': 1 if d.weekday() >= 5 else 0,
        'is_monday': 1 if d.weekday() == 0 else 0,
        'is_friday': 1 if d.weekday() == 4 else 0,
        'is_high_season': 1 if d.month in (12, 1, 2, 7, 8) else 0,
        'is_carnival': 1 if d.month == 2 and 5 <= d.day <= 20 else 0,
        'is_holiday': 1 if d.month in (12, 1) else 0,
    }


def load_model():
    global _model, _scaler
    if _model is None:
        if os.path.exists(MODEL_FILE):
            _model = joblib.load(MODEL_FILE)
            _scaler = joblib.load(SCALER_FILE)
            logger.info("Hotel model loaded from disk")
        else:
            logger.warning("Hotel model not found, training now...")
            import asyncio
            asyncio.create_task(train_hotel_model())
    return _model, _scaler


async def train_hotel_model():
    """Train the hotel occupancy forecasting model."""
    global _model, _scaler
    
    from sqlalchemy import create_engine
    import os
    
    DATABASE_URL = os.getenv('DATABASE_URL')
    engine = create_engine(DATABASE_URL)
    
    df = pd.read_sql("""
        SELECT kpi_date, occupancy_rate
        FROM hotel.daily_kpis
        ORDER BY kpi_date
    """, engine)
    
    if len(df) < 30:
        return {"error": "Insufficient data for training"}
    
    df['kpi_date'] = pd.to_datetime(df['kpi_date'])
    
    # Build features
    feature_rows = []
    for _, row in df.iterrows():
        d = row['kpi_date'].date()
        features = get_calendar_features(d)
        features['occupancy_rate'] = float(row['occupancy_rate'])
        feature_rows.append(features)
    
    feat_df = pd.DataFrame(feature_rows)
    
    # Add lag features
    feat_df = feat_df.sort_values('dayofyear').reset_index(drop=True)
    feat_df['lag_7'] = feat_df['occupancy_rate'].shift(7).fillna(feat_df['occupancy_rate'].mean())
    feat_df['lag_14'] = feat_df['occupancy_rate'].shift(14).fillna(feat_df['occupancy_rate'].mean())
    feat_df['lag_30'] = feat_df['occupancy_rate'].shift(30).fillna(feat_df['occupancy_rate'].mean())
    feat_df['rolling_7'] = feat_df['occupancy_rate'].rolling(7, min_periods=1).mean()
    feat_df['rolling_30'] = feat_df['occupancy_rate'].rolling(30, min_periods=1).mean()
    
    feature_cols = [
        'dayofweek', 'month', 'quarter', 'dayofyear', 'weekofyear',
        'is_weekend', 'is_monday', 'is_friday', 'is_high_season',
        'is_carnival', 'is_holiday', 'lag_7', 'lag_14', 'lag_30',
        'rolling_7', 'rolling_30'
    ]
    
    X = feat_df[feature_cols].values
    y = feat_df['occupancy_rate'].values
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    model = GradientBoostingRegressor(
        n_estimators=200,
        learning_rate=0.05,
        max_depth=4,
        subsample=0.8,
        random_state=42
    )
    model.fit(X_train_scaled, y_train)
    
    y_pred = model.predict(X_test_scaled)
    rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
    mae = float(mean_absolute_error(y_test, y_pred))
    r2 = float(r2_score(y_test, y_pred))
    
    joblib.dump(model, MODEL_FILE)
    joblib.dump(scaler, SCALER_FILE)
    
    _model = model
    _scaler = scaler
    
    logger.info(f"Hotel model trained: RMSE={rmse:.3f}%, MAE={mae:.3f}%, R2={r2:.3f}")
    
    return {
        "status": "trained",
        "samples": len(df),
        "metrics": {"rmse": rmse, "mae": mae, "r2": r2}
    }


@router.post("/train/hotel-occupancy", summary="Train hotel occupancy forecast model")
async def trigger_training():
    """Triggers model training. Takes 10-30 seconds."""
    result = await train_hotel_model()
    return result


@router.post("/predict/hotel-occupancy", summary="Predict hotel occupancy for next 14 days")
async def predict_hotel_occupancy(
    horizon_days: int = 14,
    db: Session = Depends(get_db)
):
    """
    Returns predicted occupancy (%) for the next N days.
    Uses the trained Gradient Boosting model.
    """
    model, scaler = load_model()
    
    if model is None:
        # Return heuristic forecast if model not trained yet
        today = date.today()
        predictions = []
        for i in range(1, horizon_days + 1):
            d = today + timedelta(days=i)
            base = 70.0
            if d.weekday() >= 5:
                base += 12
            if d.month in (12, 1, 2):
                base += 8
            base += np.random.normal(0, 3)
            predictions.append({
                "date": str(d),
                "predicted_occupancy_pct": round(max(35, min(97, base)), 1),
                "confidence": "low"
            })
        return {"model": "heuristic_fallback", "predictions": predictions}
    
    # Get recent data for lag features
    recent = db.execute(text("""
        SELECT kpi_date, occupancy_rate
        FROM hotel.daily_kpis
        ORDER BY kpi_date DESC
        LIMIT 30
    """)).fetchall()
    
    recent_occ = [float(r.occupancy_rate) for r in reversed(recent)]
    
    today = date.today()
    predictions = []
    
    for i in range(1, horizon_days + 1):
        d = today + timedelta(days=i)
        features = get_calendar_features(d)
        
        lag_7 = recent_occ[-7] if len(recent_occ) >= 7 else np.mean(recent_occ)
        lag_14 = recent_occ[-14] if len(recent_occ) >= 14 else np.mean(recent_occ)
        lag_30 = recent_occ[-30] if len(recent_occ) >= 30 else np.mean(recent_occ)
        rolling_7 = np.mean(recent_occ[-7:]) if len(recent_occ) >= 7 else np.mean(recent_occ)
        rolling_30 = np.mean(recent_occ[-30:]) if len(recent_occ) >= 30 else np.mean(recent_occ)
        
        X = np.array([[
            features['dayofweek'], features['month'], features['quarter'],
            features['dayofyear'], features['weekofyear'], features['is_weekend'],
            features['is_monday'], features['is_friday'], features['is_high_season'],
            features['is_carnival'], features['is_holiday'],
            lag_7, lag_14, lag_30, rolling_7, rolling_30
        ]])
        
        X_scaled = scaler.transform(X)
        pred = float(model.predict(X_scaled)[0])
        pred = max(35.0, min(97.0, pred))
        
        predictions.append({
            "date": str(d),
            "predicted_occupancy_pct": round(pred, 1),
            "day_of_week": d.strftime('%A'),
            "confidence": "high"
        })
        
        recent_occ.append(pred)
    
    return {
        "model": "GradientBoostingRegressor",
        "horizon_days": horizon_days,
        "predictions": predictions
    }
