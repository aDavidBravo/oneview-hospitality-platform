from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..database import get_db

router = APIRouter()

@router.get("/")
def get_rooms(db: Session = Depends(get_db)):
    rows = db.execute(text("""
        SELECT r.id, r.room_number, r.room_type, r.capacity, r.base_rate, r.floor, r.is_active,
               COUNT(res.id) AS total_reservations
        FROM hotel.rooms r
        LEFT JOIN hotel.reservations res ON res.room_id = r.id
        GROUP BY r.id
        ORDER BY r.room_number
    """)).fetchall()
    return [dict(r._mapping) for r in rows]

@router.get("/availability")
def room_availability(
    checkin: str,
    checkout: str,
    db: Session = Depends(get_db)
):
    rows = db.execute(text("""
        SELECT r.id, r.room_number, r.room_type, r.base_rate, r.capacity
        FROM hotel.rooms r
        WHERE r.is_active = TRUE
          AND r.id NOT IN (
              SELECT room_id FROM hotel.reservations
              WHERE status NOT IN ('cancelled', 'checked_out')
                AND checkin_date < :co AND checkout_date > :ci
          )
        ORDER BY r.base_rate
    """), {"ci": checkin, "co": checkout}).fetchall()
    return [dict(r._mapping) for r in rows]
