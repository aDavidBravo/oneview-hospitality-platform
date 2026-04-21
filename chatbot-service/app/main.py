"""
Chatbot Service - NLP interface for KPI queries
Translates natural language questions to API calls
"""
import os
import re
import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from datetime import date, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HOTEL_URL = os.getenv('HOTEL_SERVICE_URL', 'http://hotel-service:8001')
RESTAURANT_URL = os.getenv('RESTAURANT_SERVICE_URL', 'http://restaurant-service:8002')
REALESTATE_URL = os.getenv('REALESTATE_SERVICE_URL', 'http://realestate-service:8003')
ANALYTICS_URL = os.getenv('ANALYTICS_SERVICE_URL', 'http://analytics-service:8004')

app = FastAPI(
    title="OneView Chatbot Service",
    description="""NLP Chatbot for KPI queries in natural language.
    Translates questions about hotel, restaurant and real estate KPIs to API calls.""",
    version="1.0.0"
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class ChatMessage(BaseModel):
    message: str
    session_id: str = "default"


# ==========================================
# Intent Detection (Rule-based NLP)
# ==========================================

INTENTS = [
    {
        "name": "hotel_occupancy",
        "keywords": ["ocupación", "ocupacion", "ocupado", "hotel", "habitaciones", "huespedes"],
        "handler": "handle_hotel_occupancy"
    },
    {
        "name": "hotel_adr",
        "keywords": ["adr", "tarifa promedio", "precio por noche", "tarifa diaria"],
        "handler": "handle_hotel_adr"
    },
    {
        "name": "hotel_revenue",
        "keywords": ["ingresos hotel", "revenue hotel", "facturacion hotel"],
        "handler": "handle_hotel_revenue"
    },
    {
        "name": "hotel_forecast",
        "keywords": ["forecast hotel", "prediccion hotel", "pronóstico hotel", "ocupación futura", "proximos dias"],
        "handler": "handle_hotel_forecast"
    },
    {
        "name": "restaurant_sales",
        "keywords": ["ventas restaurante", "restaurante", "cena", "almuerzo", "desayuno", "bar"],
        "handler": "handle_restaurant_sales"
    },
    {
        "name": "realestate_units",
        "keywords": ["unidades", "departamentos", "disponibles", "vendidas", "inmobiliaria", "proyecto"],
        "handler": "handle_realestate_units"
    },
    {
        "name": "realestate_funnel",
        "keywords": ["leads", "funnel", "conversión", "clientes inmobiliaria"],
        "handler": "handle_realestate_funnel"
    },
    {
        "name": "help",
        "keywords": ["ayuda", "help", "que puedes", "comandos", "preguntar"],
        "handler": "handle_help"
    },
]


def detect_intent(message: str) -> str:
    msg_lower = message.lower()
    for intent in INTENTS:
        for kw in intent['keywords']:
            if kw in msg_lower:
                return intent['handler']
    return "handle_unknown"


def extract_period(message: str) -> tuple:
    """Extract date range from message."""
    msg = message.lower()
    today = date.today()
    
    if "hoy" in msg or "today" in msg:
        return today, today
    elif "ayer" in msg or "yesterday" in msg:
        return today - timedelta(days=1), today - timedelta(days=1)
    elif "último mes" in msg or "ultimo mes" in msg or "last month" in msg:
        return today - timedelta(days=30), today
    elif "última semana" in msg or "ultima semana" in msg or "last week" in msg:
        return today - timedelta(days=7), today
    elif "últimos 7" in msg:
        return today - timedelta(days=7), today
    elif "últimos 30" in msg:
        return today - timedelta(days=30), today
    else:
        return today - timedelta(days=30), today  # default last 30 days


# ==========================================
# Intent Handlers
# ==========================================

async def handle_hotel_occupancy(message: str) -> str:
    start, end = extract_period(message)
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                f"{HOTEL_URL}/hotel/kpis/range",
                params={"start_date": str(start), "end_date": str(end)}
            )
            data = r.json()
        
        if data.get('data'):
            avg_occ = sum(d['occupancy_rate'] for d in data['data']) / len(data['data'])
            max_occ = max(d['occupancy_rate'] for d in data['data'])
            min_occ = min(d['occupancy_rate'] for d in data['data'])
            return (
                f"🏨 **Ocupación del Hotel** (del {start} al {end}):\n\n"
                f"• Promedio: **{avg_occ:.1f}%**\n"
                f"• Máxima: {max_occ:.1f}%\n"
                f"• Mínima: {min_occ:.1f}%\n\n"
                f"_{len(data['data'])} días analizados_"
            )
    except Exception as e:
        logger.error(f"Error fetching hotel occupancy: {e}")
    
    return "⚠️ No pude obtener datos de ocupación en este momento. Verifica que el hotel-service esté activo."


async def handle_hotel_forecast(message: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(f"{ANALYTICS_URL}/analytics/predict/hotel-occupancy")
            data = r.json()
        
        preds = data.get('predictions', [])
        if preds:
            result = f"🔮 **Forecast de Ocupación - Próximos {len(preds)} días:**\n\n"
            for p in preds[:7]:  # Show first 7
                bar = "█" * int(p['predicted_occupancy_pct'] / 10)
                result += f"• {p['date']} ({p.get('day_of_week', '')}): **{p['predicted_occupancy_pct']}%** {bar}\n"
            return result
    except Exception as e:
        logger.error(f"Forecast error: {e}")
    
    return "⚠️ No pude generar el forecast. Asegúrate de entrenar el modelo primero."


async def handle_hotel_adr(message: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"{HOTEL_URL}/hotel/kpis/summary")
            data = r.json()
        
        adr = data['kpis']['adr']
        revpar = data['kpis']['revpar']
        return (
            f"💰 **KPIs de Tarifa - Hotel (30 días):**\n\n"
            f"• ADR (Tarifa Promedio): **${adr['value']:.2f} USD**"
            + (f" ({adr['delta_pct']:+.1f}% vs per. anterior)" if adr.get('delta_pct') else "") + "\n"
            f"• RevPAR: **${revpar['value']:.2f} USD**"
            + (f" ({revpar['delta_pct']:+.1f}% vs per. anterior)" if revpar.get('delta_pct') else "")
        )
    except:
        return "⚠️ No pude obtener datos de ADR/RevPAR."


async def handle_hotel_revenue(message: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"{HOTEL_URL}/hotel/kpis/summary")
            data = r.json()
        
        rev = data['kpis']['total_revenue']
        return (
            f"📊 **Ingresos del Hotel (30 días):**\n\n"
            f"• Total: **${rev['value']:,.2f} USD**"
            + (f"\n• Variación: {rev['delta_pct']:+.1f}% vs período anterior" if rev.get('delta_pct') else "")
        )
    except:
        return "⚠️ No pude obtener datos de ingresos del hotel."


async def handle_restaurant_sales(message: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"{RESTAURANT_URL}/restaurant/kpis/summary")
            data = r.json()
        
        return (
            f"🍽️ **Ventas del Restaurante (30 días):**\n\n"
            f"• Total: **${data['total_revenue']:,.2f} USD**\n"
            f"• Tickets: {data['total_tickets']:,}\n"
            f"• Comensales: {data['total_covers']:,}\n"
            f"• Ticket Promedio: ${data['avg_ticket']:.2f} USD"
            + (f"\n• Vs período anterior: {data['revenue_vs_prev_period_pct']:+.1f}%" 
               if data.get('revenue_vs_prev_period_pct') else "")
        )
    except:
        return "⚠️ No pude obtener datos de ventas del restaurante."


async def handle_realestate_units(message: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"{REALESTATE_URL}/realestate/kpis/units-status")
            data = r.json()
        
        result = "🏢 **Estado de Unidades Inmobiliarias:**\n\n"
        for proj in data.get('summary', []):
            result += (
                f"📍 **{proj['project']}**\n"
                f"   Disponibles: {proj['available']} | Reservadas: {proj['reserved']} | "
                f"Vendidas: {proj['sold']} ({proj['sold_pct']}%)\n\n"
            )
        return result
    except:
        return "⚠️ No pude obtener datos de unidades inmobiliarias."


async def handle_realestate_funnel(message: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"{REALESTATE_URL}/realestate/kpis/funnel")
            data = r.json()
        
        result = f"📈 **Funnel de Ventas Inmobiliario:**\n\n"
        for stage in data.get('funnel', []):
            bar_len = int(stage['conversion_rate'] / 5)
            bar = "█" * bar_len
            result += f"• {stage['stage']}: **{stage['count']:,}** ({stage['conversion_rate']:.1f}%) {bar}\n"
        result += f"\n🎯 Conversión global: **{data['overall_conversion_pct']:.2f}%**"
        return result
    except:
        return "⚠️ No pude obtener datos del funnel."


async def handle_help(message: str) -> str:
    return """🤖 **OneView Assistant - Preguntas que puedo responder:**

🏨 **Hotel:**
• "¿Cuál fue la ocupación del último mes?"
• "¿Cuál es el ADR actual?"
• "¿Cuánto facturo el hotel?"
• "¿Cuál es el forecast de ocupación?"

🍽️ **Restaurante:**
• "¿Cuánto vendio el restaurante la ultima semana?"
• "¿Cuáles son las ventas por servicio?"

🏢 **Inmobiliaria:**
• "¿Cuántas unidades disponibles hay?"
• "¿Cuántos leads tenemos en el funnel?"
• "¿Cuánto es la conversión de leads?"
"""


async def handle_unknown(message: str) -> str:
    return (
        f"🤔 No entendí bien la pregunta: *\"{message}\"*\n\n"
        "Escribe **ayuda** para ver qué preguntas puedo responder."
    )


HANDLERS = {
    "handle_hotel_occupancy": handle_hotel_occupancy,
    "handle_hotel_adr": handle_hotel_adr,
    "handle_hotel_revenue": handle_hotel_revenue,
    "handle_hotel_forecast": handle_hotel_forecast,
    "handle_restaurant_sales": handle_restaurant_sales,
    "handle_realestate_units": handle_realestate_units,
    "handle_realestate_funnel": handle_realestate_funnel,
    "handle_help": handle_help,
    "handle_unknown": handle_unknown,
}


@app.post("/chat/message", tags=["Chat"])
async def chat(msg: ChatMessage):
    """Process a natural language message and return KPI data."""
    intent = detect_intent(msg.message)
    handler = HANDLERS.get(intent, handle_unknown)
    response = await handler(msg.message)
    
    return {
        "user_message": msg.message,
        "intent_detected": intent,
        "response": response,
        "session_id": msg.session_id
    }


@app.get("/chat", response_class=HTMLResponse, tags=["UI"])
async def chat_ui():
    """Simple web UI for the chatbot."""
    return HTMLResponse(content=CHAT_HTML)


@app.get("/health")
async def health(): return {"status": "healthy", "service": "chatbot-service"}


CHAT_HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OneView Assistant</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'Segoe UI', sans-serif; background: #0f1117; color: #e0e0e0; height: 100vh; display: flex; flex-direction: column; }
        .header { background: linear-gradient(135deg, #1a1f2e, #252d3d); padding: 1rem 1.5rem; border-bottom: 1px solid #2d3748; display: flex; align-items: center; gap: 12px; }
        .header h1 { font-size: 1.2rem; font-weight: 600; color: #fff; }
        .header .badge { background: #3b82f6; color: #fff; font-size: 0.7rem; padding: 2px 8px; border-radius: 12px; }
        .chat-container { flex: 1; overflow-y: auto; padding: 1.5rem; display: flex; flex-direction: column; gap: 1rem; }
        .message { max-width: 80%; padding: 0.75rem 1rem; border-radius: 12px; line-height: 1.5; white-space: pre-wrap; }
        .message.user { align-self: flex-end; background: #3b82f6; color: #fff; border-radius: 12px 12px 2px 12px; }
        .message.bot { align-self: flex-start; background: #1e2535; border: 1px solid #2d3748; border-radius: 12px 12px 12px 2px; }
        .message.bot strong { color: #60a5fa; }
        .input-area { padding: 1rem 1.5rem; background: #1a1f2e; border-top: 1px solid #2d3748; display: flex; gap: 12px; }
        .input-area input { flex: 1; background: #252d3d; border: 1px solid #374151; border-radius: 8px; padding: 0.75rem 1rem; color: #e0e0e0; font-size: 0.95rem; outline: none; }
        .input-area input:focus { border-color: #3b82f6; }
        .input-area button { background: #3b82f6; color: #fff; border: none; border-radius: 8px; padding: 0.75rem 1.5rem; cursor: pointer; font-size: 0.95rem; font-weight: 500; transition: background 0.2s; }
        .input-area button:hover { background: #2563eb; }
        .suggestions { display: flex; flex-wrap: wrap; gap: 8px; padding: 0 1.5rem 1rem; }
        .suggestion { background: #1e2535; border: 1px solid #374151; border-radius: 20px; padding: 0.4rem 0.9rem; font-size: 0.82rem; cursor: pointer; color: #9ca3af; transition: all 0.2s; }
        .suggestion:hover { border-color: #3b82f6; color: #60a5fa; }
        .loading { color: #6b7280; font-style: italic; }
        .logo { width: 32px; height: 32px; background: linear-gradient(135deg, #3b82f6, #8b5cf6); border-radius: 8px; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">OV</div>
        <div>
            <h1>OneView Assistant</h1>
            <div style="font-size:0.75rem;color:#6b7280;">Consulta KPIs en lenguaje natural</div>
        </div>
        <span class="badge">AI</span>
    </div>
    
    <div class="chat-container" id="chat">
        <div class="message bot">👋 Hola! Soy el asistente de OneView. Puedo responder preguntas sobre los KPIs del hotel, restaurante e inmobiliaria.

Escribe <strong>ayuda</strong> para ver ejemplos de preguntas.</div>
    </div>
    
    <div class="suggestions">
        <span class="suggestion" onclick="sendMsg(this.textContent)">¿Ocupación del hotel último mes?</span>
        <span class="suggestion" onclick="sendMsg(this.textContent)">¿Ventas del restaurante?</span>
        <span class="suggestion" onclick="sendMsg(this.textContent)">¿Forecast de ocupación?</span>
        <span class="suggestion" onclick="sendMsg(this.textContent)">¿Unidades disponibles?</span>
        <span class="suggestion" onclick="sendMsg(this.textContent)">¿Cuál es el ADR?</span>
    </div>
    
    <div class="input-area">
        <input type="text" id="input" placeholder="Escribe tu pregunta sobre KPIs..." onkeydown="if(event.key==='Enter') sendMsg()" />
        <button onclick="sendMsg()">Enviar</button>
    </div>
    
    <script>
        async function sendMsg(text) {
            const input = document.getElementById('input');
            const msg = text || input.value.trim();
            if (!msg) return;
            input.value = '';
            
            const chat = document.getElementById('chat');
            
            // User message
            const userDiv = document.createElement('div');
            userDiv.className = 'message user';
            userDiv.textContent = msg;
            chat.appendChild(userDiv);
            
            // Loading
            const loadDiv = document.createElement('div');
            loadDiv.className = 'message bot loading';
            loadDiv.textContent = 'Consultando datos...';
            chat.appendChild(loadDiv);
            chat.scrollTop = chat.scrollHeight;
            
            try {
                const res = await fetch('/chat/message', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message: msg})
                });
                const data = await res.json();
                
                loadDiv.className = 'message bot';
                loadDiv.innerHTML = data.response.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/\n/g, '<br>');
            } catch(e) {
                loadDiv.textContent = '⚠️ Error al procesar la consulta. Intenta nuevamente.';
            }
            
            chat.scrollTop = chat.scrollHeight;
        }
    </script>
</body>
</html>
"""
