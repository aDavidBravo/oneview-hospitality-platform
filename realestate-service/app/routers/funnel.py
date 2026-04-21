"""
Real Estate Service - Funnel Router
Leads -> Interactions -> Contracts conversion analytics
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional

from ..database import get_db

router = APIRouter()


@router.get("/kpis/funnel", summary="Sales funnel KPIs by project")
async def get_funnel(
    project_id: Optional[int] = Query(default=None, description="Filter by project ID"),
    db: Session = Depends(get_db)
):
    """
    Returns the full conversion funnel:
    Total Leads -> Contacted -> Qualified -> Visits -> Converted
    with conversion rates per stage.
    """
    filter_clause = "WHERE 1=1"
    params = {}
    if project_id:
        filter_clause += " AND project_id = :pid"
        params['pid'] = project_id
    
    result = db.execute(text(f"""
        SELECT
            COUNT(*) as total_leads,
            SUM(CASE WHEN status != 'new' THEN 1 ELSE 0 END) as contacted,
            SUM(CASE WHEN status IN ('qualified', 'converted') THEN 1 ELSE 0 END) as qualified,
            SUM(CASE WHEN status = 'converted' THEN 1 ELSE 0 END) as converted,
            SUM(CASE WHEN status = 'lost' THEN 1 ELSE 0 END) as lost
        FROM realestate.leads
        {filter_clause}
    """), params).fetchone()
    
    # Count showroom visits
    visit_filter = "WHERE i.interaction_type = 'showroom_visit'"
    if project_id:
        visit_filter += " AND l.project_id = :pid"
    
    visits_result = db.execute(text(f"""
        SELECT COUNT(DISTINCT l.id) as leads_with_visit
        FROM realestate.interactions i
        JOIN realestate.leads l ON i.lead_id = l.id
        {visit_filter}
    """), params).fetchone()
    
    total = result.total_leads or 1
    contacted = result.contacted or 0
    qualified = result.qualified or 0
    visited = visits_result.leads_with_visit or 0
    converted = result.converted or 0
    
    return {
        "project_id": project_id,
        "funnel": [
            {"stage": "Leads", "count": total, "conversion_rate": 100.0},
            {"stage": "Contactados", "count": contacted, "conversion_rate": round(contacted / total * 100, 1)},
            {"stage": "Calificados", "count": qualified, "conversion_rate": round(qualified / total * 100, 1)},
            {"stage": "Visitas", "count": visited, "conversion_rate": round(visited / total * 100, 1)},
            {"stage": "Contratos", "count": converted, "conversion_rate": round(converted / total * 100, 1)},
        ],
        "leads_lost": result.lost,
        "overall_conversion_pct": round(converted / total * 100, 2)
    }


@router.get("/kpis/by-source", summary="Lead performance by acquisition channel")
async def get_by_source(
    project_id: Optional[int] = Query(default=None),
    db: Session = Depends(get_db)
):
    filter_clause = "WHERE 1=1"
    params = {}
    if project_id:
        filter_clause += " AND project_id = :pid"
        params['pid'] = project_id
    
    results = db.execute(text(f"""
        SELECT 
            source_channel,
            COUNT(*) as total_leads,
            SUM(CASE WHEN status = 'converted' THEN 1 ELSE 0 END) as converted,
            AVG(CASE WHEN status = 'converted' THEN 1.0 ELSE 0.0 END) * 100 as conv_rate
        FROM realestate.leads
        {filter_clause}
        GROUP BY source_channel
        ORDER BY conv_rate DESC
    """), params).fetchall()
    
    return {
        "data": [
            {
                "channel": r.source_channel,
                "total_leads": r.total_leads,
                "converted": r.converted,
                "conversion_rate_pct": round(float(r.conv_rate), 1)
            }
            for r in results
        ]
    }


@router.get("/kpis/revenue", summary="Revenue from contracts by project")
async def get_revenue(
    project_id: Optional[int] = Query(default=None),
    db: Session = Depends(get_db)
):
    filter_clause = "WHERE c.status != 'cancelled'"
    params = {}
    if project_id:
        filter_clause += " AND u.project_id = :pid"
        params['pid'] = project_id
    
    results = db.execute(text(f"""
        SELECT 
            p.name as project_name,
            p.city,
            COUNT(c.id) as contracts,
            SUM(c.final_price) as total_revenue,
            AVG(c.final_price) as avg_price,
            AVG(c.discount_pct) as avg_discount
        FROM realestate.contracts c
        JOIN realestate.units u ON c.unit_id = u.id
        JOIN realestate.projects p ON u.project_id = p.id
        {filter_clause}
        GROUP BY p.id, p.name, p.city
        ORDER BY total_revenue DESC
    """), params).fetchall()
    
    return {
        "data": [
            {
                "project": r.project_name,
                "city": r.city,
                "contracts": r.contracts,
                "total_revenue": round(float(r.total_revenue or 0), 2),
                "avg_price": round(float(r.avg_price or 0), 2),
                "avg_discount_pct": round(float(r.avg_discount or 0), 2)
            }
            for r in results
        ]
    }
