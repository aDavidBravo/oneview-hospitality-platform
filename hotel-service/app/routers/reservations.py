from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..database import get_db
from typing import Optional

router = APIRouter()

@router.get("/")
def get_reservations(
    start:   str = Query(description="YYYY-MM-DD"),
    end:     str = Query(description="YYYY-MM-DD"),
    channel: Optional[str] = Query(default=None),
    country: Optional[str] = Query(default=None),
    status:  Optional[str] = Query(default=None),
    limit:   int = Query(default=100, le=1000),
    db: Session = Depends(get_db)
):
    filters = "WHERE r.checkin_date BETWEEN :s AND :e"
    params  = {"s": start, "e": end}
    if channel:
        filters += " AND r.channel = :ch"
        params["ch"] = channel
    if country:
        filters += " AND g.country = :co"
        params["co"] = country
    if status:
        filters += " AND r.status = :st"
        params["st"] = status

    rows = db.execute(text(f"""
        SELECT r.id, r.checkin_date, r.checkout_date, r.nights,
               r.status, r.channel, r.rate_charged, r.total_amount,
               ro.room_type, ro.room_number,
               g.country, g.travel_purpose
        FROM hotel.reservations r
        JOIN hotel.rooms ro ON ro.id = r.room_id
        JOIN hotel.guests g ON g.id = r.guest_id
        {filters}
        ORDER BY r.checkin_date DESC
        LIMIT :lim
    """), {**params, "lim": limit}).fetchall()
    return [dict(r._mapping) for r in rows]


@router.get("/by-channel")
def reservations_by_channel(
    start: str = Query(description="YYYY-MM-DD"),
    end:   str = Query(description="YYYY-MM-DD"),
    db: Session = Depends(get_db)
):
    rows = db.execute(text("""
        SELECT channel,
               COUNT(*)::int             AS total_reservations,
               AVG(rate_charged)::numeric(10,2) AS avg_rate,
               SUM(total_amount)::numeric(14,2) AS total_revenue
        FROM hotel.reservations
        WHERE checkin_date BETWEEN :s AND :e
        GROUP BY channel
        ORDER BY total_revenue DESC
    """), {"s": start, "e": end}).fetchall()
    return [dict(r._mapping) for r in rows]


@router.get("/by-country")
def reservations_by_country(
    start: str = Query(description="YYYY-MM-DD"),
    end:   str = Query(description="YYYY-MM-DD"),
    db: Session = Depends(get_db)
):
    rows = db.execute(text("""
        SELECT g.country,
               COUNT(r.id)::int               AS reservations,
               SUM(r.total_amount)::numeric(14,2) AS revenue
        FROM hotel.reservations r
        JOIN hotel.guests g ON g.id = r.guest_id
        WHERE r.checkin_date BETWEEN :s AND :e
        GROUP BY g.country
        ORDER BY reservations DESC
        LIMIT 20
    """), {"s": start, "e": end}).fetchall()
    return [dict(r._mapping) for r in rows]
