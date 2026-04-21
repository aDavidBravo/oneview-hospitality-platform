"""
Restaurant Service - Sales Routers
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import date, timedelta
from typing import Optional

from ..database import get_db

router = APIRouter()


@router.get("/kpis/daily-sales", summary="Daily sales breakdown by service type")
async def get_daily_sales(
    sale_date: date = Query(default=None, description="Date YYYY-MM-DD"),
    db: Session = Depends(get_db)
):
    if not sale_date:
        sale_date = date.today() - timedelta(days=1)
    
    results = db.execute(text("""
        SELECT service_type, total_tickets, total_covers, total_revenue, avg_ticket
        FROM restaurant.daily_sales_summary
        WHERE sale_date = :date
        ORDER BY total_revenue DESC
    """), {'date': sale_date}).fetchall()
    
    if not results:
        raise HTTPException(status_code=404, detail=f"No sales data for {sale_date}")
    
    total_day_revenue = sum(float(r.total_revenue) for r in results)
    
    return {
        "date": str(sale_date),
        "total_revenue": round(total_day_revenue, 2),
        "by_service": [
            {
                "service_type": r.service_type,
                "total_tickets": r.total_tickets,
                "total_covers": r.total_covers,
                "total_revenue": round(float(r.total_revenue), 2),
                "avg_ticket": round(float(r.avg_ticket or 0), 2),
                "revenue_share_pct": round(float(r.total_revenue) / total_day_revenue * 100, 1)
            }
            for r in results
        ]
    }


@router.get("/kpis/monthly-sales", summary="Monthly sales aggregation")
async def get_monthly_sales(
    year: int = Query(default=2024),
    service_type: Optional[str] = Query(default=None),
    db: Session = Depends(get_db)
):
    filter_clause = "EXTRACT(YEAR FROM sale_date) = :year"
    params = {'year': year}
    if service_type:
        filter_clause += " AND service_type = :svc"
        params['svc'] = service_type
    
    results = db.execute(text(f"""
        SELECT 
            EXTRACT(MONTH FROM sale_date)::int as month,
            service_type,
            SUM(total_tickets) as tickets,
            SUM(total_covers) as covers,
            SUM(total_revenue) as revenue,
            AVG(avg_ticket) as avg_ticket
        FROM restaurant.daily_sales_summary
        WHERE {filter_clause}
        GROUP BY month, service_type
        ORDER BY month, revenue DESC
    """), params).fetchall()
    
    return {
        "year": year,
        "data": [
            {
                "month": r.month,
                "service_type": r.service_type,
                "total_tickets": int(r.tickets),
                "total_covers": int(r.covers),
                "total_revenue": round(float(r.revenue), 2),
                "avg_ticket": round(float(r.avg_ticket or 0), 2)
            }
            for r in results
        ]
    }


@router.get("/kpis/summary", summary="Restaurant executive summary (last 30 days)")
async def get_restaurant_summary(db: Session = Depends(get_db)):
    today = date.today()
    
    current = db.execute(text("""
        SELECT 
            SUM(total_revenue) as total_rev,
            SUM(total_tickets) as total_tickets,
            SUM(total_covers) as total_covers,
            AVG(avg_ticket) as avg_ticket
        FROM restaurant.daily_sales_summary
        WHERE sale_date BETWEEN :start AND :end
    """), {'start': today - timedelta(days=30), 'end': today - timedelta(days=1)}).fetchone()
    
    previous = db.execute(text("""
        SELECT SUM(total_revenue) as total_rev
        FROM restaurant.daily_sales_summary
        WHERE sale_date BETWEEN :start AND :end
    """), {'start': today - timedelta(days=60), 'end': today - timedelta(days=31)}).fetchone()
    
    rev_delta = None
    if previous.total_rev and previous.total_rev > 0:
        rev_delta = round((float(current.total_rev or 0) - float(previous.total_rev)) / float(previous.total_rev) * 100, 1)
    
    return {
        "period": "last_30_days",
        "total_revenue": round(float(current.total_rev or 0), 2),
        "total_tickets": int(current.total_tickets or 0),
        "total_covers": int(current.total_covers or 0),
        "avg_ticket": round(float(current.avg_ticket or 0), 2),
        "revenue_vs_prev_period_pct": rev_delta
    }


@router.get("/kpis/trend", summary="Sales trend for last N days")
async def get_sales_trend(
    days: int = Query(default=30, le=180),
    db: Session = Depends(get_db)
):
    today = date.today()
    results = db.execute(text("""
        SELECT sale_date, SUM(total_revenue) as daily_total
        FROM restaurant.daily_sales_summary
        WHERE sale_date BETWEEN :start AND :end
        GROUP BY sale_date
        ORDER BY sale_date
    """), {'start': today - timedelta(days=days), 'end': today - timedelta(days=1)}).fetchall()
    
    return {
        "days": days,
        "trend": [
            {"date": str(r.sale_date), "total_revenue": round(float(r.daily_total), 2)}
            for r in results
        ]
    }
