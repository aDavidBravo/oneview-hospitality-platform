"""
Simple NLP intent classifier using keyword matching.
Can be upgraded to a transformer model or Claude API.
"""
from datetime import date, timedelta
from typing import Tuple, Dict

TODAY = date.today()


def process_query(question: str) -> Tuple[str, Dict]:
    q = question.lower()

    # — Hotel intents
    if any(w in q for w in ['hotel', 'ocupación', 'habitación', 'adr', 'revpar']):
        if any(w in q for w in ['hoy', 'hoy', 'actual']):
            return 'hotel_kpis_daily', {'date': str(TODAY)}
        elif any(w in q for w in ['forecast', 'predicción', 'próximos', 'futuro']):
            return 'hotel_forecast', {}
        elif any(w in q for w in ['mes', 'mensual', 'mes pasado', 'último mes']):
            last = TODAY.replace(day=1) - timedelta(days=1)
            return 'hotel_kpis_summary', {
                'start': str(last.replace(day=1)),
                'end':   str(last)
            }
        elif any(w in q for w in ['resumen', 'promedio', 'año', 'anual']):
            return 'hotel_kpis_summary', {
                'start': str(TODAY.replace(month=1, day=1)),
                'end':   str(TODAY)
            }
        else:
            return 'hotel_kpis_daily', {'date': str(TODAY)}

    # — Restaurant intents
    elif any(w in q for w in ['restaurante', 'comida', 'ventas', 'menú', 'cubierto']):
        if any(w in q for w in ['producto', 'más vendido', 'popular', 'top']):
            return 'restaurant_top_products', {}
        else:
            return 'restaurant_by_service', {
                'start': str(TODAY - timedelta(days=30)),
                'end':   str(TODAY)
            }

    # — Real estate intents
    elif any(w in q for w in ['inmobiliaria', 'unidad', 'departamento', 'lead', 'contrato', 'venta']):
        if any(w in q for w in ['funnel', 'etapa', 'estado de leads']):
            return 'realestate_funnel', {}
        elif any(w in q for w in ['disponible', 'disponibles', 'inventario']):
            return 'realestate_units', {}
        else:
            return 'realestate_funnel', {}

    return 'unknown', {}
