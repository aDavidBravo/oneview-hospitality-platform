from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..database import get_db

router = APIRouter()

@router.get("/rooms", summary="List all rooms with type info")
async def get_rooms(db: Session = Depends(get_db)):
    results = db.execute(text("""
        SELECT r.id, r.room_number, r.floor, r.status,
               rt.code, rt.name, rt.capacity, rt.base_rate
        FROM hotel.rooms r
        JOIN hotel.room_types rt ON r.room_type_id = rt.id
        ORDER BY r.room_number
    """)).fetchall()
    
    return {
        "total": len(results),
        "rooms": [
            {
                "id": r.id,
                "room_number": r.room_number,
                "floor": r.floor,
                "status": r.status,
                "type_code": r.code,
                "type_name": r.name,
                "capacity": r.capacity,
                "base_rate": float(r.base_rate)
            }
            for r in results
        ]
    }

@router.get("/rooms/availability", summary="Room availability summary by type")
async def get_room_availability(db: Session = Depends(get_db)):
    results = db.execute(text("""
        SELECT rt.name, rt.code, rt.base_rate,
               COUNT(r.id) as total,
               SUM(CASE WHEN r.status = 'available' THEN 1 ELSE 0 END) as available,
               SUM(CASE WHEN r.status = 'occupied' THEN 1 ELSE 0 END) as occupied
        FROM hotel.room_types rt
        LEFT JOIN hotel.rooms r ON r.room_type_id = rt.id
        GROUP BY rt.id, rt.name, rt.code, rt.base_rate
        ORDER BY rt.base_rate
    """)).fetchall()
    
    return {
        "summary": [
            {
                "type_code": r.code,
                "type_name": r.name,
                "base_rate": float(r.base_rate),
                "total_rooms": r.total,
                "available": r.available,
                "occupied": r.occupied
            }
            for r in results
        ]
    }
