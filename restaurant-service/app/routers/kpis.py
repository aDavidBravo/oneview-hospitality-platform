from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..database import get_db
from datetime import date
from typing import Optional

router = APIRouter()

@router.get("/daily-sales")
def daily_sales(
    query_date: str = Query(default=None, alias="date"),
    db: Session = Depends(get_db)
):
    if not query_date:
        query_date = str(date.today())
    rows = db.execute(text("""
        SELECT sale_date, service_type, total_revenue, total_covers, avg_ticket
        FROM restaurant.daily_sales_summary
        WHERE sale_date = :d
        ORDER BY service_type
    """), {"d": query_date}).fetchall()
    return [dict(r._mapping) for r in rows]


@router.get("/weekly-sales")
def weekly_sales(
    start: str = Query(description="YYYY-MM-DD"),
    end:   str = Query(description="YYYY-MM-DD"),
    db: Session = Depends(get_db)
):
    rows = db.execute(text("""
        SELECT
            DATE_TRUNC('week', sale_date)::date AS week_start,
            service_type,
            SUM(total_revenue)::numeric(12,2)  AS revenue,
            SUM(total_covers)                  AS covers,
            AVG(avg_ticket)::numeric(8,2)      AS avg_ticket
        FROM restaurant.daily_sales_summary
        WHERE sale_date BETWEEN :s AND :e
        GROUP BY 1, 2
        ORDER BY 1, 2
    """), {"s": start, "e": end}).fetchall()
    return [dict(r._mapping) for r in rows]


@router.get("/by-service")
def kpis_by_service(
    start: str = Query(description="YYYY-MM-DD"),
    end:   str = Query(description="YYYY-MM-DD"),
    db: Session = Depends(get_db)
):
    rows = db.execute(text("""
        SELECT service_type,
               SUM(total_revenue)::numeric(12,2) AS total_revenue,
               SUM(total_covers)                 AS total_covers,
               AVG(avg_ticket)::numeric(8,2)     AS avg_ticket,
               COUNT(*)                          AS days
        FROM restaurant.daily_sales_summary
        WHERE sale_date BETWEEN :s AND :e
        GROUP BY service_type
        ORDER BY total_revenue DESC
    """), {"s": start, "e": end}).fetchall()
    return [dict(r._mapping) for r in rows]


@router.get("/monthly")
def monthly_summary(
    year:  int = Query(2024),
    month: int = Query(1),
    db: Session = Depends(get_db)
):
    rows = db.execute(text("""
        SELECT
            DATE_TRUNC('month', sale_date)::date AS month,
            SUM(total_revenue)::numeric(12,2)    AS total_revenue,
            SUM(total_covers)                    AS total_covers,
            AVG(avg_ticket)::numeric(8,2)        AS avg_ticket
        FROM restaurant.daily_sales_summary
        WHERE EXTRACT(YEAR  FROM sale_date) = :y
          AND EXTRACT(MONTH FROM sale_date) = :m
        GROUP BY 1
    """), {"y": year, "m": month}).fetchall()
    return [dict(r._mapping) for r in rows]


@router.get("/day-of-week")
def sales_by_dow(
    start: str = Query(description="YYYY-MM-DD"),
    end:   str = Query(description="YYYY-MM-DD"),
    db: Session = Depends(get_db)
):
    rows = db.execute(text("""
        SELECT
            TO_CHAR(sale_date, 'Day')            AS day_name,
            EXTRACT(DOW FROM sale_date)::int     AS dow,
            AVG(total_revenue)::numeric(10,2)    AS avg_revenue,
            AVG(total_covers)::numeric(6,1)      AS avg_covers
        FROM restaurant.daily_sales_summary
        WHERE sale_date BETWEEN :s AND :e
        GROUP BY day_name, dow
        ORDER BY dow
    """), {"s": start, "e": end}).fetchall()
    return [dict(r._mapping) for r in rows]
