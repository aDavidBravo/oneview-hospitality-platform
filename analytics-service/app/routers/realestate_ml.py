"""
Real Estate Lead Conversion Scoring — Random Forest Classifier
"""
import os
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session
from sqlalchemy import text
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, classification_report
from sklearn.preprocessing import LabelEncoder
from ..database import get_db, MODELS_PATH

router = APIRouter()
MODEL_FILE = os.path.join(MODELS_PATH, "realestate_lead_model.pkl")
ENC_FILE   = os.path.join(MODELS_PATH, "realestate_lead_encoders.pkl")

FEATURES = ['source_channel','interest_level','unit_type_interest',
            'interactions_count','visits_count','days_in_funnel']


def _load_training_data(db: Session) -> pd.DataFrame:
    rows = db.execute(text("""
        SELECT
            l.id,
            l.source_channel,
            l.interest_level,
            l.unit_type_interest,
            l.funnel_stage,
            l.lead_date,
            COUNT(i.id)::int                        AS interactions_count,
            SUM(CASE WHEN i.interaction_type='visit' THEN 1 ELSE 0 END)::int AS visits_count,
            EXTRACT(DAY FROM NOW() - l.lead_date::timestamp)::int AS days_in_funnel
        FROM realestate.leads l
        LEFT JOIN realestate.interactions i ON i.lead_id = l.id
        GROUP BY l.id
    """)).fetchall()
    df = pd.DataFrame([dict(r._mapping) for r in rows])
    if df.empty:
        return df
    df['is_closed'] = (df['funnel_stage'] == 'closed').astype(int)
    return df


@router.post("/realestate-conversion")
def predict_lead_conversion(
    payload: dict = Body(default={
        "source_channel":      "web",
        "interest_level":      "hot",
        "unit_type_interest":  "2br",
        "interactions_count":  5,
        "visits_count":        2,
        "days_in_funnel":      30
    }),
    db: Session = Depends(get_db)
):
    """Predicts the probability that a lead will close a contract."""
    model_path = Path(MODEL_FILE)
    enc_path   = Path(ENC_FILE)

    if not model_path.exists():
        # Train on-the-fly
        df = _load_training_data(db)
        if df.empty or len(df) < 50:
            return {"error": "Insufficient training data"}

        encoders = {}
        for col in ['source_channel','interest_level','unit_type_interest']:
            le = LabelEncoder()
            df[col] = le.fit_transform(df[col].fillna('unknown'))
            encoders[col] = le

        df = df.fillna(0)
        X = df[FEATURES]
        y = df['is_closed']

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        model = RandomForestClassifier(n_estimators=200, max_depth=8,
                                       class_weight='balanced', random_state=42)
        model.fit(X_train, y_train)

        y_prob = model.predict_proba(X_test)[:,1]
        auc = roc_auc_score(y_test, y_prob)

        model_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(model, model_path)
        joblib.dump(encoders, enc_path)
    else:
        model    = joblib.load(model_path)
        encoders = joblib.load(enc_path)
        auc      = None

    # Encode input
    row = {}
    for col in ['source_channel','interest_level','unit_type_interest']:
        val = payload.get(col, 'unknown')
        le  = encoders[col]
        if val in le.classes_:
            row[col] = le.transform([val])[0]
        else:
            row[col] = 0

    row['interactions_count'] = int(payload.get('interactions_count', 0))
    row['visits_count']       = int(payload.get('visits_count', 0))
    row['days_in_funnel']     = int(payload.get('days_in_funnel', 0))

    X_pred = pd.DataFrame([row])[FEATURES]
    prob   = float(model.predict_proba(X_pred)[0, 1])

    return {
        "model":               "Random Forest Classifier",
        "conversion_probability": round(prob, 4),
        "conversion_pct":      round(prob * 100, 2),
        "recommendation":     (
            "Alta prioridad — agendar reunión" if prob > 0.65 else
            "Seguimiento activo" if prob > 0.40 else
            "Nurturing automático"
        ),
        "train_roc_auc":      round(auc, 4) if auc else "model loaded from cache",
    }
