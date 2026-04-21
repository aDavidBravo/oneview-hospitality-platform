from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..database import get_db

router = APIRouter()

@router.get("/")
def list_projects(db: Session = Depends(get_db)):
    rows = db.execute(text("""
        SELECT p.*,
               COUNT(u.id)::int                                   AS total_units,
               SUM(CASE WHEN u.status='sold'      THEN 1 ELSE 0 END)::int AS sold,
               SUM(CASE WHEN u.status='reserved'  THEN 1 ELSE 0 END)::int AS reserved,
               SUM(CASE WHEN u.status='available' THEN 1 ELSE 0 END)::int AS available
        FROM realestate.projects p
        LEFT JOIN realestate.units u ON u.project_id = p.id
        GROUP BY p.id
        ORDER BY p.id
    """)).fetchall()
    return [dict(r._mapping) for r in rows]


@router.get("/{project_id}")
def get_project(project_id: int, db: Session = Depends(get_db)):
    row = db.execute(text("""
        SELECT p.*,
               COUNT(u.id)::int AS total_units,
               SUM(CASE WHEN u.status='sold' THEN 1 ELSE 0 END)::int AS sold
        FROM realestate.projects p
        LEFT JOIN realestate.units u ON u.project_id = p.id
        WHERE p.id = :pid
        GROUP BY p.id
    """), {"pid": project_id}).fetchone()
    if not row:
        return {"error": "Project not found"}
    return dict(row._mapping)
