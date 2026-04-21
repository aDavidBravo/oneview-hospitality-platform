from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..database import get_db
from typing import Optional

router = APIRouter()

@router.get("/status")
def units_status(
    project_id: Optional[int] = Query(default=None),
    db: Session = Depends(get_db)
):
    params: dict = {}
    filter_clause = "WHERE 1=1"
    if project_id:
        filter_clause += " AND project_id = :pid"
        params["pid"] = project_id

    rows = db.execute(text(f"""
        SELECT unit_type, status,
               COUNT(*)::int                         AS count,
               AVG(list_price)::numeric(14,2)        AS avg_price,
               SUM(list_price)::numeric(16,2)        AS total_list_value
        FROM realestate.units
        {filter_clause}
        GROUP BY unit_type, status
        ORDER BY unit_type, status
    """), params).fetchall()
    return [dict(r._mapping) for r in rows]


@router.get("/available")
def available_units(
    project_id: Optional[int] = Query(default=None),
    unit_type:  Optional[str]  = Query(default=None),
    db: Session = Depends(get_db)
):
    params: dict = {"st": "available"}
    filter_clause = "WHERE u.status = :st"
    if project_id:
        filter_clause += " AND u.project_id = :pid"
        params["pid"] = project_id
    if unit_type:
        filter_clause += " AND u.unit_type = :ut"
        params["ut"] = unit_type

    rows = db.execute(text(f"""
        SELECT u.id, u.unit_code, u.unit_type, u.floor, u.area_sqm, u.list_price,
               p.name AS project_name, p.city
        FROM realestate.units u
        JOIN realestate.projects p ON p.id = u.project_id
        {filter_clause}
        ORDER BY u.list_price
        LIMIT 200
    """), params).fetchall()
    return [dict(r._mapping) for r in rows]
