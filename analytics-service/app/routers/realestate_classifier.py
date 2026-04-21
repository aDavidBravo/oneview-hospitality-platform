"""
Analytics Service - Real Estate Lead Scoring
Gradient Boosting Classifier for conversion probability
"""
import os
import joblib
import numpy as np
import pandas as pd
from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, accuracy_score, classification_report
from typing import Optional
import logging

from ..database import get_db, MODEL_PATH

logger = logging.getLogger(__name__)
router = APIRouter()

MODEL_FILE = os.path.join(MODEL_PATH, 'realestate_classifier.pkl')
_classifier = None
_encoders = {}


class LeadScoringInput(BaseModel):
    source_channel: str = "web"  # web, referral, social_media, billboard, event
    interest_level: str = "warm"  # cold, warm, hot
    unit_type_interest: str = "2br"  # studio, 1br, 2br, 3br, office_m
    n_interactions: int = 3
    n_showroom_visits: int = 0
    days_in_funnel: int = 15
    budget_max: float = 200000.0
    project_id: int = 1


async def train_classifier():
    global _classifier, _encoders
    
    DATABASE_URL = os.getenv('DATABASE_URL')
    from sqlalchemy import create_engine
    engine = create_engine(DATABASE_URL)
    
    leads_df = pd.read_sql("""
        SELECT 
            l.id, l.source_channel, l.interest_level, l.unit_type_interest,
            l.budget_max, l.project_id, l.status, l.created_at,
            COUNT(i.id) as n_interactions,
            SUM(CASE WHEN i.interaction_type = 'showroom_visit' THEN 1 ELSE 0 END) as n_visits,
            EXTRACT(DAY FROM (MAX(i.interaction_date) - MIN(i.interaction_date))) + 1 as funnel_days
        FROM realestate.leads l
        LEFT JOIN realestate.interactions i ON l.id = i.lead_id
        GROUP BY l.id, l.source_channel, l.interest_level, l.unit_type_interest,
                 l.budget_max, l.project_id, l.status, l.created_at
    """, engine)
    
    if len(leads_df) < 50:
        return {"error": "Insufficient leads for training"}
    
    leads_df['converted'] = (leads_df['status'] == 'converted').astype(int)
    leads_df['n_interactions'] = leads_df['n_interactions'].fillna(0)
    leads_df['n_visits'] = leads_df['n_visits'].fillna(0)
    leads_df['funnel_days'] = leads_df['funnel_days'].fillna(0)
    leads_df['budget_max'] = leads_df['budget_max'].fillna(200000)
    
    # Encode categoricals
    cat_cols = ['source_channel', 'interest_level', 'unit_type_interest']
    encoders = {}
    for col in cat_cols:
        le = LabelEncoder()
        leads_df[col + '_enc'] = le.fit_transform(leads_df[col].fillna('unknown'))
        encoders[col] = le
    
    feature_cols = [
        'source_channel_enc', 'interest_level_enc', 'unit_type_interest_enc',
        'n_interactions', 'n_visits', 'funnel_days', 'budget_max', 'project_id'
    ]
    
    X = leads_df[feature_cols].values
    y = leads_df['converted'].values
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    clf = GradientBoostingClassifier(
        n_estimators=200,
        learning_rate=0.05,
        max_depth=4,
        subsample=0.8,
        random_state=42
    )
    clf.fit(X_train, y_train)
    
    y_pred = clf.predict(X_test)
    y_prob = clf.predict_proba(X_test)[:, 1]
    
    auc = float(roc_auc_score(y_test, y_prob))
    acc = float(accuracy_score(y_test, y_pred))
    
    _classifier = {'model': clf, 'encoders': encoders, 'feature_cols': feature_cols}
    joblib.dump(_classifier, MODEL_FILE)
    
    logger.info(f"RE Classifier trained: AUC={auc:.3f}, Accuracy={acc:.3f}")
    
    return {
        "status": "trained",
        "samples": len(leads_df),
        "metrics": {"auc_roc": auc, "accuracy": acc}
    }


@router.post("/train/realestate-conversion", summary="Train lead conversion classifier")
async def trigger_training():
    return await train_classifier()


@router.post("/predict/realestate-conversion", summary="Score a lead's probability of converting")
async def predict_conversion(lead: LeadScoringInput):
    """
    Returns conversion probability 0-100% for a given lead.
    Also includes key drivers and recommendation.
    """
    global _classifier
    
    if _classifier is None and os.path.exists(MODEL_FILE):
        _classifier = joblib.load(MODEL_FILE)
    
    if _classifier is None:
        # Heuristic scoring when model not trained
        score = 0.20
        if lead.source_channel in ['referral', 'event']:
            score += 0.20
        if lead.interest_level == 'hot':
            score += 0.25
        elif lead.interest_level == 'warm':
            score += 0.10
        if lead.n_showroom_visits > 0:
            score += 0.20
        if lead.n_interactions >= 5:
            score += 0.10
        
        score = min(0.90, score)
        return {
            "model": "heuristic_fallback",
            "conversion_probability": round(score * 100, 1),
            "recommendation": _get_recommendation(score)
        }
    
    # Encode inputs
    encoders = _classifier['encoders']
    
    def safe_encode(encoder, val, default=0):
        try:
            return int(encoder.transform([val])[0])
        except:
            return default
    
    X = np.array([[
        safe_encode(encoders['source_channel'], lead.source_channel),
        safe_encode(encoders['interest_level'], lead.interest_level),
        safe_encode(encoders['unit_type_interest'], lead.unit_type_interest),
        lead.n_interactions,
        lead.n_showroom_visits,
        lead.days_in_funnel,
        lead.budget_max,
        lead.project_id
    ]])
    
    prob = float(_classifier['model'].predict_proba(X)[0][1])
    
    return {
        "model": "GradientBoostingClassifier",
        "conversion_probability": round(prob * 100, 1),
        "risk_level": "high" if prob > 0.6 else "medium" if prob > 0.35 else "low",
        "recommendation": _get_recommendation(prob),
        "key_factors": [
            f"Canal: {lead.source_channel} (impacto alto)",
            f"Visitas al showroom: {lead.n_showroom_visits}",
            f"Interacciones totales: {lead.n_interactions}",
            f"Nivel de interés: {lead.interest_level}"
        ]
    }


@router.get("/predict/realestate-leads-bulk", summary="Score all active leads")
async def score_all_leads(
    project_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Returns conversion scores for all active leads (for dashboard table)."""
    filter_clause = "WHERE l.status NOT IN ('converted', 'lost')"
    params = {}
    if project_id:
        filter_clause += " AND l.project_id = :pid"
        params['pid'] = project_id
    
    leads = db.execute(text(f"""
        SELECT l.id, l.first_name || ' ' || l.last_name as name,
               l.source_channel, l.interest_level, l.unit_type_interest,
               l.budget_max, l.project_id, l.assigned_to, l.created_at,
               COUNT(i.id) as n_interactions,
               SUM(CASE WHEN i.interaction_type = 'showroom_visit' THEN 1 ELSE 0 END) as n_visits
        FROM realestate.leads l
        LEFT JOIN realestate.interactions i ON l.id = i.lead_id
        {filter_clause}
        GROUP BY l.id, l.first_name, l.last_name, l.source_channel, l.interest_level,
                 l.unit_type_interest, l.budget_max, l.project_id, l.assigned_to, l.created_at
        ORDER BY l.created_at DESC
        LIMIT 100
    """), params).fetchall()
    
    scored_leads = []
    for lead in leads:
        input_data = LeadScoringInput(
            source_channel=lead.source_channel or 'web',
            interest_level=lead.interest_level or 'warm',
            unit_type_interest=lead.unit_type_interest or '2br',
            n_interactions=int(lead.n_interactions or 0),
            n_showroom_visits=int(lead.n_visits or 0),
            budget_max=float(lead.budget_max or 200000),
            project_id=lead.project_id or 1
        )
        score_result = await predict_conversion(input_data)
        
        scored_leads.append({
            "lead_id": lead.id,
            "name": lead.name,
            "source_channel": lead.source_channel,
            "interest_level": lead.interest_level,
            "assigned_to": lead.assigned_to,
            "n_interactions": int(lead.n_interactions or 0),
            "n_visits": int(lead.n_visits or 0),
            "conversion_probability": score_result['conversion_probability'],
            "risk_level": score_result.get('risk_level', 'medium')
        })
    
    return {
        "total_scored": len(scored_leads),
        "leads": sorted(scored_leads, key=lambda x: x['conversion_probability'], reverse=True)
    }


def _get_recommendation(prob: float) -> str:
    if prob > 0.70:
        return "🔥 Lead caliente - Priorizar contacto inmediato con oferta personalizada"
    elif prob > 0.50:
        return "✅ Lead calificado - Agendar visita al showroom esta semana"
    elif prob > 0.30:
        return "⚠️ Lead tibio - Continuar nurturing, enviar materiales de proyecto"
    else:
        return "❌ Probabilidad baja - Incluir en campaña de reactivación a largo plazo"
