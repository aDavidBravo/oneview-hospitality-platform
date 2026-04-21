from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..database import get_db
from typing import Optional

router = APIRouter()

@router.get("/funnel")
def funnel_kpis(
    project_id: Optional[int] = Query(default=None),
    db: Session = Depends(get_db)
):
    filter_clause = "WHERE 1=1"
    params: dict = {}
    if project_id:
        filter_clause += " AND project_id = :pid"
        params["pid"] = project_id

    rows = db.execute(text(f"""
        SELECT funnel_stage,
               COUNT(*)::int         AS leads_count,
               ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS pct_of_total
        FROM realestate.leads
        {filter_clause}
        GROUP BY funnel_stage
        ORDER BY
            CASE funnel_stage
                WHEN 'lead'     THEN 1
                WHEN 'contact'  THEN 2
                WHEN 'visit'    THEN 3
                WHEN 'proposal' THEN 4
                WHEN 'reserved' THEN 5
                WHEN 'closed'   THEN 6
                WHEN 'lost'     THEN 7
                ELSE 8
            END
    """), params).fetchall()
    return [dict(r._mapping) for r in rows]


@router.get("/conversion-rates")
def conversion_rates(
    project_id: Optional[int] = Query(default=None),
    db: Session = Depends(get_db)
):
    params: dict = {}
    filter_clause = "WHERE 1=1"
    if project_id:
        filter_clause += " AND project_id = :pid"
        params["pid"] = project_id

    rows = db.execute(text(f"""
        WITH stage_counts AS (
            SELECT funnel_stage, COUNT(*) AS cnt
            FROM realestate.leads
            {filter_clause}
            GROUP BY funnel_stage
        )
        SELECT
            funnel_stage,
            cnt,
            LAG(cnt) OVER (ORDER BY
                CASE funnel_stage
                    WHEN 'lead' THEN 1 WHEN 'contact' THEN 2 WHEN 'visit' THEN 3
                    WHEN 'proposal' THEN 4 WHEN 'reserved' THEN 5 WHEN 'closed' THEN 6 ELSE 7
                END) AS prev_stage_cnt,
            CASE WHEN LAG(cnt) OVER (ORDER BY
                CASE funnel_stage
                    WHEN 'lead' THEN 1 WHEN 'contact' THEN 2 WHEN 'visit' THEN 3
                    WHEN 'proposal' THEN 4 WHEN 'reserved' THEN 5 WHEN 'closed' THEN 6 ELSE 7
                END) > 0
            THEN ROUND(cnt * 100.0 / LAG(cnt) OVER (ORDER BY
                CASE funnel_stage
                    WHEN 'lead' THEN 1 WHEN 'contact' THEN 2 WHEN 'visit' THEN 3
                    WHEN 'proposal' THEN 4 WHEN 'reserved' THEN 5 WHEN 'closed' THEN 6 ELSE 7
                END), 2)
            ELSE NULL END AS conversion_rate_pct
        FROM stage_counts
        ORDER BY
            CASE funnel_stage
                WHEN 'lead' THEN 1 WHEN 'contact' THEN 2 WHEN 'visit' THEN 3
                WHEN 'proposal' THEN 4 WHEN 'reserved' THEN 5 WHEN 'closed' THEN 6 ELSE 7
            END
    """), params).fetchall()
    return [dict(r._mapping) for r in rows]


@router.get("/revenue")
def revenue_summary(
    project_id: Optional[int] = Query(default=None),
    db: Session = Depends(get_db)
):
    params: dict = {}
    filter_clause = "WHERE 1=1"
    if project_id:
        filter_clause += " AND l.project_id = :pid"
        params["pid"] = project_id

    row = db.execute(text(f"""
        SELECT
            COUNT(c.id)::int                           AS total_contracts,
            SUM(c.final_price)::numeric(16,2)          AS total_revenue,
            AVG(c.final_price)::numeric(14,2)          AS avg_ticket,
            AVG(c.discount_pct)::numeric(5,2)          AS avg_discount_pct,
            SUM(c.final_price) FILTER (WHERE c.payment_method='cash')::numeric(16,2) AS cash_revenue,
            SUM(c.final_price) FILTER (WHERE c.payment_method='financing')::numeric(16,2) AS financing_revenue
        FROM realestate.contracts c
        JOIN realestate.leads l ON l.id = c.lead_id
        {filter_clause}
    """), params).fetchone()
    return dict(row._mapping)


@router.get("/leads-by-channel")
def leads_by_channel(
    project_id: Optional[int] = Query(default=None),
    db: Session = Depends(get_db)
):
    params: dict = {}
    filter_clause = "WHERE 1=1"
    if project_id:
        filter_clause += " AND project_id = :pid"
        params["pid"] = project_id

    rows = db.execute(text(f"""
        SELECT source_channel,
               COUNT(*)::int   AS total_leads,
               SUM(CASE WHEN funnel_stage = 'closed' THEN 1 ELSE 0 END)::int AS closed,
               ROUND(SUM(CASE WHEN funnel_stage = 'closed' THEN 1 ELSE 0 END)
                     * 100.0 / COUNT(*), 2) AS close_rate_pct
        FROM realestate.leads
        {filter_clause}
        GROUP BY source_channel
        ORDER BY total_leads DESC
    """), params).fetchall()
    return [dict(r._mapping) for r in rows]
