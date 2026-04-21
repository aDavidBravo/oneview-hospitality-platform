"""
Restaurant Service - Products Router
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional

from ..database import get_db

router = APIRouter()


@router.get("/kpis/top-products", summary="Top products by revenue")
async def get_top_products(
    period_days: int = Query(default=30, description="Look-back period in days"),
    service_type: Optional[str] = Query(default=None),
    limit: int = Query(default=10, le=50),
    db: Session = Depends(get_db)
):
    filter_clause = ""
    params = {'days': period_days, 'limit': limit}
    if service_type:
        filter_clause = "AND mi.service_type = :svc"
        params['svc'] = service_type
    
    results = db.execute(text(f"""
        SELECT 
            mi.name,
            mi.service_type,
            mi.sale_price,
            mi.cost_price,
            mi.margin_pct,
            COUNT(ti.id) as units_sold,
            SUM(ti.total_price) as total_revenue
        FROM restaurant.ticket_items ti
        JOIN restaurant.menu_items mi ON ti.menu_item_id = mi.id
        JOIN restaurant.sales_tickets st ON ti.ticket_id = st.id
        WHERE st.sale_datetime >= NOW() - INTERVAL '1 day' * :days
        {filter_clause}
        GROUP BY mi.id, mi.name, mi.service_type, mi.sale_price, mi.cost_price, mi.margin_pct
        ORDER BY total_revenue DESC
        LIMIT :limit
    """), params).fetchall()
    
    # Fallback if no ticket_items yet (ticket_items requires extra generation step)
    if not results:
        results = db.execute(text("""
            SELECT name, service_type, sale_price, cost_price, margin_pct,
                   0 as units_sold, 0 as total_revenue
            FROM restaurant.menu_items
            WHERE active = true
            ORDER BY margin_pct DESC
            LIMIT :limit
        """), {'limit': limit}).fetchall()
    
    return {
        "period_days": period_days,
        "products": [
            {
                "name": r.name,
                "service_type": r.service_type,
                "sale_price": float(r.sale_price),
                "cost_price": float(r.cost_price),
                "margin_pct": float(r.margin_pct or 0),
                "units_sold": int(r.units_sold),
                "total_revenue": round(float(r.total_revenue or 0), 2)
            }
            for r in results
        ]
    }


@router.get("/menu", summary="Full menu with margin analysis")
async def get_menu(db: Session = Depends(get_db)):
    results = db.execute(text("""
        SELECT mi.id, mc.name as category, mi.name, mi.sale_price, mi.cost_price,
               mi.margin_pct, mi.service_type, mi.active
        FROM restaurant.menu_items mi
        JOIN restaurant.menu_categories mc ON mi.category_id = mc.id
        ORDER BY mc.name, mi.margin_pct DESC
    """)).fetchall()
    
    return {
        "total": len(results),
        "items": [
            {
                "id": r.id,
                "category": r.category,
                "name": r.name,
                "sale_price": float(r.sale_price),
                "cost_price": float(r.cost_price),
                "margin_pct": float(r.margin_pct or 0),
                "service_type": r.service_type,
                "active": r.active
            }
            for r in results
        ]
    }
