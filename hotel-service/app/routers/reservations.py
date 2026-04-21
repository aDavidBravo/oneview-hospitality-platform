"""
Hotel Service - Reservations Router
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import date
from typing import Optional

from ..database import get_db

router = APIRouter()


@router.get("/reservations", summary="Query reservations by date range")
async def get_reservations(
    start_date: date = Query(..., description="Start date YYYY-MM-DD"),
    end_date: date = Query(..., description="End date YYYY-MM-DD"),
    channel: Optional[str] = Query(default=None, description="Filter by channel"),
    country_code: Optional[str] = Query(default=None, description="Filter by guest country (ISO 2-letter)"),
    status: Optional[str] = Query(default=None, description="Filter by status"),
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0),
    db: Session = Depends(get_db)
):
    """
    Returns reservations for a date range with optional filters.
    """
    filters = "WHERE r.checkin_date BETWEEN :start AND :end"
    params = {'start': start_date, 'end': end_date}
    
    if channel:
        filters += " AND r.channel = :channel"
        params['channel'] = channel
    if country_code:
        filters += " AND g.country_code = :country"
        params['country'] = country_code.upper()
    if status:
        filters += " AND r.status = :status"
        params['status'] = status
    
    count_result = db.execute(text(f"""
        SELECT COUNT(*) FROM hotel.reservations r
        LEFT JOIN hotel.guests g ON r.guest_id = g.id
        {filters}
    """), params).scalar()
    
    params['limit'] = limit
    params['offset'] = offset
    
    results = db.execute(text(f"""
        SELECT 
            r.reservation_code, r.checkin_date, r.checkout_date,
            r.channel, r.trip_purpose, r.rate_per_night, r.total_amount,
            r.status, r.adults, r.children,
            g.first_name || ' ' || g.last_name as guest_name,
            g.country_code,
            rt.name as room_type
        FROM hotel.reservations r
        LEFT JOIN hotel.guests g ON r.guest_id = g.id
        LEFT JOIN hotel.rooms ro ON r.room_id = ro.id
        LEFT JOIN hotel.room_types rt ON ro.room_type_id = rt.id
        {filters}
        ORDER BY r.checkin_date DESC
        LIMIT :limit OFFSET :offset
    """), params).fetchall()
    
    return {
        "total": count_result,
        "limit": limit,
        "offset": offset,
        "data": [
            {
                "reservation_code": r.reservation_code,
                "guest_name": r.guest_name,
                "country_code": r.country_code,
                "room_type": r.room_type,
                "checkin_date": str(r.checkin_date),
                "checkout_date": str(r.checkout_date),
                "nights": (r.checkout_date - r.checkin_date).days,
                "channel": r.channel,
                "trip_purpose": r.trip_purpose,
                "rate_per_night": float(r.rate_per_night),
                "total_amount": float(r.total_amount),
                "status": r.status,
                "adults": r.adults,
                "children": r.children
            }
            for r in results
        ]
    }


@router.get("/reservations/by-country", summary="Reservations grouped by guest country")
async def get_reservations_by_country(
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db)
):
    results = db.execute(text("""
        SELECT 
            g.country_code,
            COUNT(*) as total_reservations,
            SUM(r.total_amount) as total_revenue,
            AVG(r.rate_per_night) as avg_rate
        FROM hotel.reservations r
        JOIN hotel.guests g ON r.guest_id = g.id
        WHERE r.checkin_date BETWEEN :start AND :end
          AND r.status NOT IN ('cancelled', 'no_show')
        GROUP BY g.country_code
        ORDER BY total_reservations DESC
        LIMIT 20
    """), {'start': start_date, 'end': end_date}).fetchall()
    
    return {
        "data": [
            {
                "country_code": r.country_code,
                "total_reservations": r.total_reservations,
                "total_revenue": round(float(r.total_revenue or 0), 2),
                "avg_rate": round(float(r.avg_rate or 0), 2)
            }
            for r in results
        ]
    }
