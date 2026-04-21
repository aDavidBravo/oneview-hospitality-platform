# 🤖 Chatbot Service

Rule-based NLP chatbot with a web UI for querying hotel, restaurant, and real estate KPIs using natural language.
Runs on **port 8005** · Web UI: `http://localhost:8005/chat`

---

## Supported Intents

| Intent | Example Query |
|--------|---------------|
| Hotel occupancy | *"What's our hotel occupancy?"* |
| Hotel ADR | *"Show me the average daily rate"* |
| Hotel revenue | *"What's hotel revenue this year?"* |
| Hotel forecast | *"Forecast occupancy for next 2 weeks"* |
| Restaurant sales | *"How are restaurant sales?"* |
| RE units | *"How many units are available?"* |
| RE funnel | *"Show me the lead conversion funnel"* |
| Help | *"What can you do?"* |

---

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/chat` | Web UI (dark-theme chat interface) |
| POST | `/chat/message` | JSON API: send a message, get structured response |
| GET | `/chat/health` | Service health check |

---

## Quick Start (curl)

### 1. Ask via API
```bash
curl -s -X POST http://localhost:8005/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message": "What is our hotel occupancy rate?"}' | jq
```
Sample response:
```json
{
  "intent": "hotel_occupancy",
  "response": "Current hotel occupancy rate is 74.2%. ADR: $187.35 | RevPAR: $139.02",
  "data": { "avg_occupancy_rate": 0.742, "avg_adr": 187.35 },
  "suggestions": ["Show me ADR", "Forecast occupancy", "Restaurant sales"]
}
```

### 2. Ask via gateway (with auth)
```bash
TOKEN=$(curl -s -X POST http://localhost:8000/auth/token \
  -d "username=analyst&password=analyst2024" \
  -H "Content-Type: application/x-www-form-urlencoded" | jq -r .access_token)

curl -s -X POST http://localhost:8000/chatbot/message \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Lead conversion funnel?"}' | jq
```

### 3. Open the Web UI
```bash
open http://localhost:8005/chat   # macOS
start http://localhost:8005/chat  # Windows
```

---

## Architecture

```
User message
    ↓
Intent classifier (keyword matching + NLP)
    ↓
Downstream service call (hotel / restaurant / realestate / analytics)
    ↓
Formatted response + suggestion chips
    ↓
Chat UI or JSON API
```
