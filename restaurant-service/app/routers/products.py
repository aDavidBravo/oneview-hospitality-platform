from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..database import get_db

router = APIRouter()

@router.get("/top")
def top_products(
    period: str = Query(default="last_30_days", description="last_30_days | last_90_days | ytd"),
    db: Session = Depends(get_db)
):
    period_filter = {
        "last_30_days":  "ticket_date >= CURRENT_DATE - INTERVAL '30 days'",
        "last_90_days":  "ticket_date >= CURRENT_DATE - INTERVAL '90 days'",
        "ytd":           "EXTRACT(YEAR FROM ticket_date) = EXTRACT(YEAR FROM CURRENT_DATE)",
    }.get(period, "ticket_date >= CURRENT_DATE - INTERVAL '30 days'")

    rows = db.execute(text(f"""
        SELECT m.name, m.category, m.sell_price, m.cost_price, m.margin_pct,
               SUM(ti.quantity)::int               AS units_sold,
               SUM(ti.line_total)::numeric(12,2)   AS total_revenue
        FROM restaurant.ticket_items ti
        JOIN restaurant.menu_items m ON m.id = ti.menu_item_id
        JOIN restaurant.sales_tickets t ON t.id = ti.ticket_id
        WHERE {period_filter}
        GROUP BY m.id
        ORDER BY units_sold DESC
        LIMIT 20
    """)).fetchall()
    return [dict(r._mapping) for r in rows]


@router.get("/margin-by-category")
def margin_by_category(
    start: str = Query(description="YYYY-MM-DD"),
    end:   str = Query(description="YYYY-MM-DD"),
    db: Session = Depends(get_db)
):
    rows = db.execute(text("""
        SELECT m.category,
               SUM(ti.quantity)::int             AS units_sold,
               SUM(ti.line_total)::numeric(12,2) AS revenue,
               AVG(m.margin_pct)::numeric(5,2)   AS avg_margin_pct
        FROM restaurant.ticket_items ti
        JOIN restaurant.menu_items m ON m.id = ti.menu_item_id
        JOIN restaurant.sales_tickets t ON t.id = ti.ticket_id
        WHERE t.ticket_date BETWEEN :s AND :e
        GROUP BY m.category
        ORDER BY revenue DESC
    """), {"s": start, "e": end}).fetchall()
    return [dict(r._mapping) for r in rows]


@router.get("/inventory")
def get_inventory(db: Session = Depends(get_db)):
    rows = db.execute(text("""
        SELECT ingredient, unit, stock_qty, min_stock, unit_cost,
               CASE WHEN stock_qty <= min_stock THEN true ELSE false END AS low_stock
        FROM restaurant.inventory
        ORDER BY ingredient
    """)).fetchall()
    return [dict(r._mapping) for r in rows]
