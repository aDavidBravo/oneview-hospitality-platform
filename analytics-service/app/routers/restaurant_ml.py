"""
Restaurant Sales Forecasting
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
MODEL_FILE = os.path.join(MODELS_PATH, "restaurant_sales_model.pkl")


def _load_history(db: Session) -> pd.DataFrame:
    rows = db.execute(text("""
        SELECT sale_date, SUM(total_revenue) AS total_revenue
        FROM restaurant.daily_sales_summary
        GROUP BY sale_date
        ORDER BY sale_date
    """)).fetchall()
    df = pd.DataFrame([dict(r._mapping) for r in rows])
    if df.empty:
        return df
    df['sale_date'] = pd.to_datetime(df['sale_date'])
    df = df.set_index('sale_date').sort_index()
    return df


@router.post("/restaurant-sales")
def predict_restaurant_sales(
    horizon: int = FORECAST_HORIZON,
    db: Session = Depends(get_db)
):
    if horizon > 90:
        raise HTTPException(400, "Maximum horizon is 90 days")

    df = _load_history(db)
    if df.empty or len(df) < 30:
        return {"error": "Insufficient historical data"}

    df['dow']         = df.index.dayofweek
    df['month']       = df.index.month
    df['is_weekend']  = df['dow'].isin([4,5,6]).astype(int)
    df['is_high_s']   = df['month'].isin([1,2,7,8,12]).astype(int)
    df['lag_7']       = df['total_revenue'].shift(7)
    df['roll_7']      = df['total_revenue'].rolling(7).mean()
    df = df.dropna()

    X = df[['dow','month','is_weekend','is_high_s','lag_7','roll_7']]
    y = df['total_revenue']

    model_path = Path(MODEL_FILE)
    if model_path.exists():
        model = joblib.load(model_path)
    else:
        model = Ridge(alpha=1.0)
        model.fit(X, y)
        model_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(model, model_path)

    last_date = df.index[-1]
    history   = df['total_revenue'].iloc[-14:].tolist()
    preds = []

    for i in range(1, horizon + 1):
        fd = last_date + timedelta(days=i)
        dow  = fd.dayofweek
        mon  = fd.month
        is_w = 1 if dow in [4,5,6] else 0
        is_h = 1 if mon in [1,2,7,8,12] else 0
        lag7 = history[-7] if len(history) >= 7 else np.mean(history)
        roll = np.mean(history[-7:]) if len(history) >= 7 else np.mean(history)
        x = np.array([[dow, mon, is_w, is_h, lag7, roll]])
        pred = float(max(0, model.predict(x)[0]))
        history.append(pred)
        preds.append({"date": str(fd.date()), "predicted_revenue_usd": round(pred, 2)})

    y_pred = model.predict(X)
    return {
        "model":       "Ridge Regression + Seasonal Features",
        "horizon_days": horizon,
        "train_rmse":  round(float(np.sqrt(mean_squared_error(y, y_pred))), 2),
        "train_mae":   round(float(mean_absolute_error(y, y_pred)), 2),
        "predictions": preds,
    }
