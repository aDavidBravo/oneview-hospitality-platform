"""
Hotel Occupancy Forecasting — SARIMA + feature engineering
"""
import os
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error
from ..database import get_db, MODELS_PATH, FORECAST_HORIZON

router = APIRouter()
MODEL_FILE = os.path.join(MODELS_PATH, "hotel_occupancy_model.pkl")


def _load_history(db: Session) -> pd.DataFrame:
    rows = db.execute(text("""
        SELECT kpi_date, occupancy_rate, adr, revpar, total_revenue
        FROM hotel.daily_kpis
        ORDER BY kpi_date
    """)).fetchall()
    df = pd.DataFrame([dict(r._mapping) for r in rows])
    if df.empty:
        return df
    df['kpi_date'] = pd.to_datetime(df['kpi_date'])
    df = df.set_index('kpi_date').sort_index()
    return df


def _build_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df['day_of_week']   = df.index.dayofweek
    df['month']         = df.index.month
    df['is_weekend']    = df['day_of_week'].isin([4,5,6]).astype(int)
    df['is_high_season'] = df['month'].isin([1,2,7,8,12]).astype(int)
    df['lag_7']         = df['occupancy_rate'].shift(7)
    df['lag_14']        = df['occupancy_rate'].shift(14)
    df['rolling_7']     = df['occupancy_rate'].rolling(7).mean()
    return df.dropna()


@router.post("/hotel-occupancy")
def predict_hotel_occupancy(
    horizon: int = FORECAST_HORIZON,
    db: Session = Depends(get_db)
):
    """Predict hotel occupancy for the next N days."""
    if horizon > 90:
        raise HTTPException(400, "Maximum horizon is 90 days")

    df = _load_history(db)
    if df.empty or len(df) < 30:
        return {"error": "Insufficient historical data"}

    feat_df = _build_features(df)
    X = feat_df[['day_of_week','month','is_weekend','is_high_season','lag_7','lag_14','rolling_7']]
    y = feat_df['occupancy_rate']

    # Train or load model
    model_path = Path(MODEL_FILE)
    if model_path.exists():
        model = joblib.load(model_path)
    else:
        model = Ridge(alpha=1.0)
        model.fit(X, y)
        model_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(model, model_path)

    # Build future feature rows
    last_date = df.index[-1]
    last_occ  = df['occupancy_rate'].iloc[-7:].tolist()
    predictions = []

    for i in range(1, horizon + 1):
        future_date = last_date + timedelta(days=i)
        dow   = future_date.dayofweek
        month = future_date.month
        is_we = 1 if dow in [4,5,6] else 0
        is_hs = 1 if month in [1,2,7,8,12] else 0
        lag7  = last_occ[-7] if len(last_occ) >= 7 else np.mean(last_occ)
        lag14 = last_occ[-14] if len(last_occ) >= 14 else np.mean(last_occ)
        roll7 = np.mean(last_occ[-7:]) if len(last_occ) >= 7 else np.mean(last_occ)

        x = np.array([[dow, month, is_we, is_hs, lag7, lag14, roll7]])
        pred_occ = float(model.predict(x)[0])
        pred_occ = min(97.0, max(30.0, pred_occ))
        last_occ.append(pred_occ)

        predictions.append({
            "date":                 str(future_date.date()),
            "predicted_occupancy_pct": round(pred_occ, 2),
        })

    # Evaluation metrics on training data
    y_pred = model.predict(X)
    rmse = float(np.sqrt(mean_squared_error(y, y_pred)))
    mae  = float(mean_absolute_error(y, y_pred))

    return {
        "model":       "Ridge Regression + Seasonality Features",
        "horizon_days": horizon,
        "train_rmse":  round(rmse, 4),
        "train_mae":   round(mae, 4),
        "predictions": predictions,
    }
