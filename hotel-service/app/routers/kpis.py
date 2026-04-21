"""
Hotel Service - KPI Routers
Endpoints for occupancy, ADR, RevPAR, revenue analytics
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import date, timedelta
from typing import Optional, List
import logging

from ..database import get_db

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/kpis/daily", summary="Daily KPIs for a specific date")
async def get_daily_kpis(
    kpi_date: date = Query(default=None, description="Date in YYYY-MM-DD format. Defaults to yesterday."),
    db: Session = Depends(get_db)
):
    """
    Returns hotel KPIs for a specific date:
    - **occupancy_rate**: Percentage of rooms occupied
    - **adr**: Average Daily Rate (revenue per occupied room)
    - **revpar**: Revenue Per Available Room
    - **total_revenue**: Total room revenue for the day
    """
    if not kpi_date:
        kpi_date = date.today() - timedelta(days=1)
    
    result = db.execute(text("""
        SELECT 
            kpi_date,
            total_rooms,
            occupied_rooms,
            occupancy_rate,
            adr,
            revpar,
            total_revenue
        FROM hotel.daily_kpis
        WHERE kpi_date = :kpi_date
    """), {'kpi_date': kpi_date}).fetchone()
    
    if not result:
        raise HTTPException(status_code=404, detail=f"No KPI data found for {kpi_date}")
    
    # Get same day last year for comparison
    same_day_ly = db.execute(text("""
        SELECT occupancy_rate, adr, revpar, total_revenue
        FROM hotel.daily_kpis
        WHERE kpi_date = :kpi_date
    """), {'kpi_date': kpi_date - timedelta(days=365)}).fetchone()
    
    response = {
        "date": str(result.kpi_date),
        "total_rooms": result.total_rooms,
        "occupied_rooms": result.occupied_rooms,
        "occupancy_rate": float(result.occupancy_rate),
        "adr": float(result.adr),
        "revpar": float(result.revpar),
        "total_revenue": float(result.total_revenue),
        "vs_last_year": None
    }
    
    if same_day_ly:
        response["vs_last_year"] = {
            "occupancy_rate_delta": round(float(result.occupancy_rate) - float(same_day_ly.occupancy_rate), 2),
            "adr_delta": round(float(result.adr) - float(same_day_ly.adr), 2),
            "revpar_delta": round(float(result.revpar) - float(same_day_ly.revpar), 2),
            "revenue_delta_pct": round(
                (float(result.total_revenue) - float(same_day_ly.total_revenue)) / float(same_day_ly.total_revenue) * 100, 2
            ) if same_day_ly.total_revenue else None
        }
    
    return response


@router.get("/kpis/range", summary="KPIs for a date range")
async def get_kpis_range(
    start_date: date = Query(..., description="Start date YYYY-MM-DD"),
    end_date: date = Query(..., description="End date YYYY-MM-DD"),
    db: Session = Depends(get_db)
):
    """
    Returns daily KPIs for a date range. Maximum 365 days.
    """
    if (end_date - start_date).days > 365:
        raise HTTPException(status_code=400, detail="Date range cannot exceed 365 days")
    
    results = db.execute(text("""
        SELECT kpi_date, occupied_rooms, occupancy_rate, adr, revpar, total_revenue
        FROM hotel.daily_kpis
        WHERE kpi_date BETWEEN :start_date AND :end_date
        ORDER BY kpi_date
    """), {'start_date': start_date, 'end_date': end_date}).fetchall()
    
    return {
        "start_date": str(start_date),
        "end_date": str(end_date),
        "days": len(results),
        "data": [
            {
                "date": str(r.kpi_date),
                "occupied_rooms": r.occupied_rooms,
                "occupancy_rate": float(r.occupancy_rate),
                "adr": float(r.adr),
                "revpar": float(r.revpar),
                "total_revenue": float(r.total_revenue)
            }
            for r in results
        ]
    }


@router.get("/kpis/monthly", summary="Monthly aggregated KPIs")
async def get_monthly_kpis(
    year: int = Query(default=2024, description="Year (YYYY)"),
    month: Optional[int] = Query(default=None, description="Month (1-12). If omitted, returns full year."),
    db: Session = Depends(get_db)
):
    """
    Returns monthly aggregated KPIs: avg occupancy, avg ADR, avg RevPAR, total revenue.
    """
    if month:
        where_clause = "EXTRACT(YEAR FROM kpi_date) = :year AND EXTRACT(MONTH FROM kpi_date) = :month"
        params = {'year': year, 'month': month}
    else:
        where_clause = "EXTRACT(YEAR FROM kpi_date) = :year"
        params = {'year': year}
    
    results = db.execute(text(f"""
        SELECT 
            EXTRACT(YEAR FROM kpi_date)::int as year,
            EXTRACT(MONTH FROM kpi_date)::int as month,
            AVG(occupancy_rate) as avg_occupancy,
            AVG(adr) as avg_adr,
            AVG(revpar) as avg_revpar,
            SUM(total_revenue) as total_revenue,
            MIN(occupancy_rate) as min_occupancy,
            MAX(occupancy_rate) as max_occupancy
        FROM hotel.daily_kpis
        WHERE {where_clause}
        GROUP BY year, month
        ORDER BY year, month
    """), params).fetchall()
    
    return {
        "year": year,
        "month": month,
        "data": [
            {
                "year": r.year,
                "month": r.month,
                "avg_occupancy_rate": round(float(r.avg_occupancy), 2),
                "avg_adr": round(float(r.avg_adr), 2),
                "avg_revpar": round(float(r.avg_revpar), 2),
                "total_revenue": round(float(r.total_revenue), 2),
                "min_occupancy": round(float(r.min_occupancy), 2),
                "max_occupancy": round(float(r.max_occupancy), 2)
            }
            for r in results
        ]
    }


@router.get("/kpis/summary", summary="Executive KPI summary (last 30 days)")
async def get_kpi_summary(db: Session = Depends(get_db)):
    """
    Returns executive summary for the last 30 days vs previous 30 days.
    Ideal for the executive dashboard header cards.
    """
    today = date.today()
    
    current = db.execute(text("""
        SELECT 
            AVG(occupancy_rate) as avg_occ,
            AVG(adr) as avg_adr,
            AVG(revpar) as avg_revpar,
            SUM(total_revenue) as total_rev,
            COUNT(*) as days
        FROM hotel.daily_kpis
        WHERE kpi_date BETWEEN :start AND :end
    """), {
        'start': today - timedelta(days=30),
        'end': today - timedelta(days=1)
    }).fetchone()
    
    previous = db.execute(text("""
        SELECT 
            AVG(occupancy_rate) as avg_occ,
            AVG(adr) as avg_adr,
            AVG(revpar) as avg_revpar,
            SUM(total_revenue) as total_rev
        FROM hotel.daily_kpis
        WHERE kpi_date BETWEEN :start AND :end
    """), {
        'start': today - timedelta(days=60),
        'end': today - timedelta(days=31)
    }).fetchone()
    
    def calc_delta(current_val, prev_val):
        if prev_val and prev_val > 0:
            return round((float(current_val) - float(prev_val)) / float(prev_val) * 100, 1)
        return None
    
    return {
        "period": "last_30_days",
        "kpis": {
            "occupancy_rate": {
                "value": round(float(current.avg_occ or 0), 2),
                "unit": "%",
                "delta_pct": calc_delta(current.avg_occ, previous.avg_occ)
            },
            "adr": {
                "value": round(float(current.avg_adr or 0), 2),
                "unit": "USD",
                "delta_pct": calc_delta(current.avg_adr, previous.avg_adr)
            },
            "revpar": {
                "value": round(float(current.avg_revpar or 0), 2),
                "unit": "USD",
                "delta_pct": calc_delta(current.avg_revpar, previous.avg_revpar)
            },
            "total_revenue": {
                "value": round(float(current.total_rev or 0), 2),
                "unit": "USD",
                "delta_pct": calc_delta(current.total_rev, previous.total_rev)
            }
        }
    }


@router.get("/kpis/by-channel", summary="Reservations breakdown by booking channel")
async def get_kpis_by_channel(
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db)
):
    results = db.execute(text("""
        SELECT 
            channel,
            COUNT(*) as total_reservations,
            SUM(total_amount) as total_revenue,
            AVG(rate_per_night) as avg_rate,
            AVG(checkout_date - checkin_date) as avg_nights
        FROM hotel.reservations
        WHERE checkin_date BETWEEN :start AND :end
          AND status NOT IN ('cancelled', 'no_show')
        GROUP BY channel
        ORDER BY total_revenue DESC
    """), {'start': start_date, 'end': end_date}).fetchall()
    
    total_rev = sum(float(r.total_revenue or 0) for r in results)
    
    return {
        "start_date": str(start_date),
        "end_date": str(end_date),
        "channels": [
            {
                "channel": r.channel,
                "reservations": r.total_reservations,
                "total_revenue": round(float(r.total_revenue or 0), 2),
                "revenue_share_pct": round(float(r.total_revenue or 0) / total_rev * 100, 1) if total_rev > 0 else 0,
                "avg_rate_per_night": round(float(r.avg_rate or 0), 2),
                "avg_nights": round(float(r.avg_nights or 0), 1)
            }
            for r in results
        ]
    }
