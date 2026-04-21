from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..database import get_db
from datetime import date
from typing import Optional

router = APIRouter()

@router.get("/daily")
def get_daily_kpis(
    query_date: str = Query(default=None, alias="date", description="YYYY-MM-DD"),
    db: Session = Depends(get_db)
):
    """Retorna KPIs de ocupación, ADR y RevPAR para una fecha dada."""
    if not query_date:
        query_date = str(date.today())
    result = db.execute(text("""
        SELECT kpi_date, total_rooms, occupied_rooms,
               occupancy_rate, adr, revpar, total_revenue
        FROM hotel.daily_kpis
        WHERE kpi_date = :d
    """), {"d": query_date}).fetchone()
    if not result:
        return {"error": "No data for this date"}
    return dict(result._mapping)


@router.get("/monthly")
def get_monthly_kpis(
    year: int = Query(2024),
    month: int = Query(1),
    db: Session = Depends(get_db)
):
    rows = db.execute(text("""
        SELECT
            DATE_TRUNC('month', kpi_date)::date AS month,
            AVG(occupancy_rate)::numeric(5,2)   AS avg_occupancy_pct,
            AVG(adr)::numeric(10,2)             AS avg_adr,
            AVG(revpar)::numeric(10,2)          AS avg_revpar,
            SUM(total_revenue)::numeric(14,2)   AS total_revenue,
            COUNT(*)                            AS days
        FROM hotel.daily_kpis
        WHERE EXTRACT(YEAR FROM kpi_date) = :y
          AND EXTRACT(MONTH FROM kpi_date) = :m
        GROUP BY 1
    """), {"y": year, "m": month}).fetchall()
    return [dict(r._mapping) for r in rows]


@router.get("/summary")
def get_kpis_summary(
    start: str = Query(description="YYYY-MM-DD"),
    end:   str = Query(description="YYYY-MM-DD"),
    db: Session = Depends(get_db)
):
    """KPI summary for a date range."""
    row = db.execute(text("""
        SELECT
            COUNT(*)                            AS days,
            AVG(occupancy_rate)::numeric(5,2)   AS avg_occupancy_pct,
            AVG(adr)::numeric(10,2)             AS avg_adr,
            AVG(revpar)::numeric(10,2)          AS avg_revpar,
            SUM(total_revenue)::numeric(14,2)   AS total_revenue,
            MAX(occupancy_rate)::numeric(5,2)   AS max_occupancy,
            MIN(occupancy_rate)::numeric(5,2)   AS min_occupancy
        FROM hotel.daily_kpis
        WHERE kpi_date BETWEEN :s AND :e
    """), {"s": start, "e": end}).fetchone()
    return dict(row._mapping)


@router.get("/trend")
def get_occupancy_trend(
    start: str = Query(description="YYYY-MM-DD"),
    end:   str = Query(description="YYYY-MM-DD"),
    db: Session = Depends(get_db)
):
    rows = db.execute(text("""
        SELECT kpi_date, occupancy_rate, adr, revpar, total_revenue
        FROM hotel.daily_kpis
        WHERE kpi_date BETWEEN :s AND :e
        ORDER BY kpi_date
    """), {"s": start, "e": end}).fetchall()
    return [dict(r._mapping) for r in rows]
