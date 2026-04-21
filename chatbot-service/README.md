# Chatbot Service

Servicio de **chatbot en lenguaje natural** sobre los KPIs del holding.

## Acceso

Abre http://localhost:8005 en tu navegador para la interfaz web.

## API

```bash
curl -X POST http://localhost:8005/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "¿Cuál es la ocupación del hotel hoy?"}'
```

## Preguntas de Ejemplo

- "¿Cuál fue la ocupación promedio del hotel el último mes?"
- "¿Qué día de la semana genera más ventas en el restaurante?"
- "¿Cuántas unidades disponibles hay en el proyecto inmobiliario?"
- "¿Cuál es el forecast de ocupación del hotel para los próximos 7 días?"
- "Muestra los productos más vendidos del restaurante"
- "Muestra el funnel inmobiliario"

## Arquitectura NLP

El chatbot usa clasificación de intents por keywords (sin dependencias externas).
Puede escalarse fácilmente conectando la API de Claude (Anthropic) como LLM backend
configurando `ANTHROPIC_API_KEY` en el `.env`.
