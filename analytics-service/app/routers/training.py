from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
import os, joblib
from pathlib import Path
from ..routers.hotel_ml      import _load_history as hotel_history, _build_features, MODEL_FILE as HM
from ..routers.restaurant_ml import _load_history as rest_history,  MODEL_FILE as RM
from ..routers.realestate_ml import _load_training_data, MODEL_FILE as REM, ENC_FILE
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, roc_auc_score
import numpy as np

router = APIRouter()

@router.post("/all")
def train_all_models(db: Session = Depends(get_db)):
    """Retrain all ML models from scratch."""
    results = {}

    # — Hotel
    df = hotel_history(db)
    if len(df) >= 30:
        feat = _build_features(df)
        X = feat[['day_of_week','month','is_weekend','is_high_season','lag_7','lag_14','rolling_7']]
        y = feat['occupancy_rate']
        model = Ridge(alpha=1.0).fit(X, y)
        Path(HM).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(model, HM)
        mae = mean_absolute_error(y, model.predict(X))
        results['hotel_occupancy'] = {'status': 'trained', 'mae': round(float(mae),4)}

    # — Restaurant
    df2 = rest_history(db)
    if len(df2) >= 30:
        df2['dow']       = df2.index.dayofweek
        df2['month']     = df2.index.month
        df2['is_weekend']= df2['dow'].isin([4,5,6]).astype(int)
        df2['is_high_s'] = df2['month'].isin([1,2,7,8,12]).astype(int)
        df2['lag_7']     = df2['total_revenue'].shift(7)
        df2['roll_7']    = df2['total_revenue'].rolling(7).mean()
        df2 = df2.dropna()
        X2 = df2[['dow','month','is_weekend','is_high_s','lag_7','roll_7']]
        y2 = df2['total_revenue']
        m2 = Ridge().fit(X2, y2)
        joblib.dump(m2, RM)
        results['restaurant_sales'] = {'status': 'trained', 'mae': round(float(mean_absolute_error(y2, m2.predict(X2))),2)}

    # — Real Estate
    df3 = _load_training_data(db)
    if len(df3) >= 50:
        encoders = {}
        for col in ['source_channel','interest_level','unit_type_interest']:
            le = LabelEncoder()
            df3[col] = le.fit_transform(df3[col].fillna('unknown'))
            encoders[col] = le
        df3 = df3.fillna(0)
        feats = ['source_channel','interest_level','unit_type_interest',
                 'interactions_count','visits_count','days_in_funnel']
        X3 = df3[feats]; y3 = df3['is_closed']
        Xt, Xv, yt, yv = train_test_split(X3, y3, test_size=0.2, random_state=42, stratify=y3)
        m3 = RandomForestClassifier(n_estimators=200, max_depth=8, class_weight='balanced', random_state=42)
        m3.fit(Xt, yt)
        auc = roc_auc_score(yv, m3.predict_proba(Xv)[:,1])
        joblib.dump(m3, REM)
        joblib.dump(encoders, ENC_FILE)
        results['realestate_conversion'] = {'status': 'trained', 'roc_auc': round(float(auc),4)}

    return {"trained_models": results}
