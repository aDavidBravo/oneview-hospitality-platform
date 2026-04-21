import os
import httpx
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from .nlp import process_query

app = FastAPI(
    title="OneView — AI Chatbot",
    description="Chatbot en lenguaje natural sobre los KPIs del holding",
    version="1.0.0",
)

HOTEL_URL      = os.getenv("HOTEL_SERVICE_URL",      "http://hotel-service:8001")
RESTAURANT_URL = os.getenv("RESTAURANT_SERVICE_URL", "http://restaurant-service:8002")
REALESTATE_URL = os.getenv("REALESTATE_SERVICE_URL", "http://realestate-service:8003")
ANALYTICS_URL  = os.getenv("ANALYTICS_SERVICE_URL",  "http://analytics-service:8004")

class Query(BaseModel):
    question: str


@app.get("/", response_class=HTMLResponse)
async def chatbot_ui():
    html = open("/app/app/static/chat.html").read()
    return HTMLResponse(content=html)


@app.post("/ask")
async def ask(query: Query):
    question = query.question.strip()
    intent, params = process_query(question)

    async with httpx.AsyncClient(timeout=15.0) as client:
        if intent == "hotel_kpis_daily":
            url = f"{HOTEL_URL}/hotel/kpis/daily"
            resp = await client.get(url, params=params)
            data = resp.json()
            return {"answer": _format_hotel_kpis(data), "raw": data}

        elif intent == "hotel_kpis_summary":
            resp = await client.get(f"{HOTEL_URL}/hotel/kpis/summary", params=params)
            data = resp.json()
            return {"answer": _format_hotel_summary(data), "raw": data}

        elif intent == "restaurant_by_service":
            resp = await client.get(f"{RESTAURANT_URL}/restaurant/kpis/by-service", params=params)
            data = resp.json()
            return {"answer": _format_restaurant_service(data), "raw": data}

        elif intent == "restaurant_top_products":
            resp = await client.get(f"{RESTAURANT_URL}/restaurant/products/top",
                                    params={"period": "last_30_days"})
            data = resp.json()
            return {"answer": _format_top_products(data), "raw": data}

        elif intent == "realestate_funnel":
            resp = await client.get(f"{REALESTATE_URL}/realestate/kpis/funnel")
            data = resp.json()
            return {"answer": _format_funnel(data), "raw": data}

        elif intent == "realestate_units":
            resp = await client.get(f"{REALESTATE_URL}/realestate/units/status")
            data = resp.json()
            return {"answer": _format_units(data), "raw": data}

        elif intent == "hotel_forecast":
            resp = await client.post(f"{ANALYTICS_URL}/analytics/predict/hotel-occupancy")
            data = resp.json()
            return {"answer": _format_forecast(data), "raw": data}

        else:
            return {
                "answer": (
                    "Puedo responder preguntas sobre:\n"
                    "- Ocupación del hotel (KPIs diarios, mensuales, forecast)\n"
                    "- Ventas del restaurante (por servicio, top productos)\n"
                    "- Estado de unidades inmobiliarias y funnel de leads\n"
                    "Ejemplo: '¿Cuál fue la ocupación en enero?'"
                ),
                "raw": None
            }


# ── Formatters ───────────────────────────────────────────────────────────────

def _format_hotel_kpis(d: dict) -> str:
    if 'error' in d:
        return "No hay datos para esa fecha."
    return (
        f"🏨 **KPIs del Hotel** ({d.get('kpi_date','')})\n"
        f"• Ocupación: **{d.get('occupancy_rate','N/A')}%**\n"
        f"• ADR: **${d.get('adr','N/A')}**\n"
        f"• RevPAR: **${d.get('revpar','N/A')}**\n"
        f"• Ingresos totales: **${d.get('total_revenue','N/A')}**"
    )

def _format_hotel_summary(d: dict) -> str:
    return (
        f"🏨 **Resumen del Hotel**\n"
        f"• Ocupación promedio: **{d.get('avg_occupancy_pct','N/A')}%**\n"
        f"• ADR promedio: **${d.get('avg_adr','N/A')}**\n"
        f"• RevPAR promedio: **${d.get('avg_revpar','N/A')}**\n"
        f"• Ingresos totales: **${d.get('total_revenue','N/A')}**"
    )

def _format_restaurant_service(data: list) -> str:
    if not data:
        return "Sin datos de ventas."
    lines = ["🍽️ **Ventas del Restaurante por Servicio**"]
    for r in data:
        lines.append(f"• {r['service_type'].capitalize()}: **${r['total_revenue']}** ({r['total_covers']} cubiertos)")
    return "\n".join(lines)

def _format_top_products(data: list) -> str:
    if not data:
        return "Sin datos de productos."
    lines = ["🍽️ **Top 5 Productos más vendidos (30 días)**"]
    for r in data[:5]:
        lines.append(f"• {r['name']}: {r['units_sold']} unidades — ${r['total_revenue']}")
    return "\n".join(lines)

def _format_funnel(data: list) -> str:
    if not data:
        return "Sin datos del funnel."
    lines = ["🏢 **Funnel Inmobiliario**"]
    for r in data:
        lines.append(f"• {r['funnel_stage'].capitalize()}: **{r['leads_count']}** leads ({r['pct_of_total']}%)")
    return "\n".join(lines)

def _format_units(data: list) -> str:
    if not data:
        return "Sin datos de unidades."
    total = sum(r['count'] for r in data)
    sold  = sum(r['count'] for r in data if r['status'] == 'sold')
    avail = sum(r['count'] for r in data if r['status'] == 'available')
    return (
        f"🏢 **Estado de Unidades Inmobiliarias**\n"
        f"• Total unidades: **{total}**\n"
        f"• Vendidas: **{sold}**\n"
        f"• Disponibles: **{avail}**"
    )

def _format_forecast(data: dict) -> str:
    if 'error' in data:
        return data['error']
    preds = data.get('predictions', [])
    lines = [f"🔮 **Forecast de Ocupación — próximos {len(preds)} días**"]
    for p in preds[:7]:
        lines.append(f"• {p['date']}: **{p['predicted_occupancy_pct']}%**")
    return "\n".join(lines)
