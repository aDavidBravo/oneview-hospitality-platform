"""
Real Estate Service - Units Router
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional

from ..database import get_db

router = APIRouter()


@router.get("/kpis/units-status", summary="Units status by project")
async def get_units_status(
    project_id: Optional[int] = Query(default=None),
    db: Session = Depends(get_db)
):
    filter_clause = "WHERE 1=1"
    params = {}
    if project_id:
        filter_clause += " AND u.project_id = :pid"
        params['pid'] = project_id
    
    results = db.execute(text(f"""
        SELECT 
            p.name as project_name,
            p.city,
            u.unit_type,
            u.status,
            COUNT(*) as count,
            AVG(u.list_price) as avg_price,
            AVG(u.area_sqm) as avg_area
        FROM realestate.units u
        JOIN realestate.projects p ON u.project_id = p.id
        {filter_clause}
        GROUP BY p.id, p.name, p.city, u.unit_type, u.status
        ORDER BY p.name, u.unit_type, u.status
    """), params).fetchall()
    
    # Aggregate summary
    summary = db.execute(text(f"""
        SELECT 
            p.name,
            SUM(CASE WHEN u.status = 'available' THEN 1 ELSE 0 END) as available,
            SUM(CASE WHEN u.status = 'reserved' THEN 1 ELSE 0 END) as reserved,
            SUM(CASE WHEN u.status = 'sold' THEN 1 ELSE 0 END) as sold,
            COUNT(*) as total
        FROM realestate.units u
        JOIN realestate.projects p ON u.project_id = p.id
        {filter_clause}
        GROUP BY p.id, p.name
    """), params).fetchall()
    
    return {
        "summary": [
            {
                "project": r.name,
                "total": r.total,
                "available": r.available,
                "reserved": r.reserved,
                "sold": r.sold,
                "sold_pct": round(r.sold / r.total * 100, 1) if r.total > 0 else 0
            }
            for r in summary
        ],
        "detail": [
            {
                "project": r.project_name,
                "city": r.city,
                "unit_type": r.unit_type,
                "status": r.status,
                "count": r.count,
                "avg_price": round(float(r.avg_price or 0), 2),
                "avg_area_sqm": round(float(r.avg_area or 0), 1)
            }
            for r in results
        ]
    }


@router.get("/projects", summary="List all real estate projects")
async def get_projects(db: Session = Depends(get_db)):
    results = db.execute(text("""
        SELECT id, name, city, zone, project_type, total_units, status,
               start_date, delivery_date, description
        FROM realestate.projects
        ORDER BY id
    """)).fetchall()
    
    return {
        "projects": [
            {
                "id": r.id,
                "name": r.name,
                "city": r.city,
                "zone": r.zone,
                "type": r.project_type,
                "total_units": r.total_units,
                "status": r.status,
                "start_date": str(r.start_date) if r.start_date else None,
                "delivery_date": str(r.delivery_date) if r.delivery_date else None
            }
            for r in results
        ]
    }
