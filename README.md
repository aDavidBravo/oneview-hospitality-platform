# 🏨 OneView Hospitality Platform

> **Analítica e IA para un holding de hotel 5★, restaurante de alta gama e inmobiliaria**

[![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green?logo=fastapi)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue?logo=postgresql)](https://postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue?logo=docker)](https://docker.com)
[![React](https://img.shields.io/badge/React-18-cyan?logo=react)](https://react.dev)
[![Scikit-Learn](https://img.shields.io/badge/scikit--learn-1.3-orange?logo=scikit-learn)](https://scikit-learn.org)

---

## 📋 Contexto de Negocio

**OneView** es una plataforma de inteligencia de negocios diseñada para un holding de hospitalidad y real estate que opera:

| Unidad de Negocio | Descripción |
|---|---|
| 🏨 **Hotel 5★** | Hotel de lujo con 120 habitaciones, suites, eventos y servicios premium |
| 🍽️ **Restaurante Fine Dining** | Restaurante dentro del hotel con salón, bar, room service y catering |
| 🏢 **Complejo Inmobiliario** | Torres residenciales y de oficinas con unidades premium en venta |

El objetivo es que la dirección del holding tenga una **única vista ejecutiva** de KPIs, forecasts y alertas en tiempo real — de ahí el nombre **OneView**.

---

## 🏗️ Arquitectura de Microservicios

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENTE / BROWSER                        │
│              dashboard-ui  (React + Recharts)                   │
└─────────────────────────┬───────────────────────────────────────┘
                          │ HTTP
┌─────────────────────────▼───────────────────────────────────────┐
│                     GATEWAY API (FastAPI)                       │
│          Rate Limiting · Auth JWT · Request Routing             │
│                       PORT: 8000                                │
└──────┬──────────┬──────────┬──────────┬────────────┬───────────┘
       │          │          │          │            │
  ┌────▼───┐ ┌───▼────┐ ┌───▼────┐ ┌───▼────┐ ┌────▼────┐
  │ hotel  │ │restau- │ │reales- │ │analyt- │ │chatbot  │
  │service │ │rant    │ │tate    │ │ics     │ │service  │
  │:8001   │ │service │ │service │ │service │ │:8005    │
  │        │ │:8002   │ │:8003   │ │:8004   │ │         │
  └────┬───┘ └───┬────┘ └───┬────┘ └───┬────┘ └────┬────┘
       │          │          │          │            │
  ┌────▼──────────▼──────────▼──────────▼────────────▼────┐
  │              PostgreSQL 15 (shared DB, schemas)        │
  │   hotel_schema · restaurant_schema · realestate_schema │
  │                       PORT: 5432                       │
  └────────────────────────────────────────────────────────┘
```

### Decisión de Arquitectura: DB Compartida con Schemas

Se eligió **una base de datos PostgreSQL con schemas separados** (en lugar de bases separadas) porque:
- El holding necesita **queries cross-domain** (ej: huéspedes que también son compradores inmobiliarios)
- Simplifica el despliegue local con Docker
- Para producción, se puede migrar a **bases separadas** fácilmente cambiando las connection strings

---

## 🛠️ Stack Tecnológico

| Capa | Tecnología | Justificación |
|---|---|---|
| **Backend APIs** | Python 3.11 + FastAPI | Alto rendimiento, tipado estático, OpenAPI automático |
| **Base de Datos** | PostgreSQL 15 | Robustez, soporte JSON, extensiones analíticas |
| **ORM** | SQLAlchemy 2.0 + Alembic | Migraciones versionadas, soporte async |
| **ML / AI** | scikit-learn, pandas, statsmodels | Ecosistema maduro, reproducible |
| **Dashboard** | React 18 + Recharts + TailwindCSS | SPA moderna, gráficos interactivos |
| **Chatbot** | FastAPI + OpenAI-compatible API | NLP sobre KPIs en lenguaje natural |
| **Infraestructura** | Docker + Docker Compose | Reproducibilidad 100% local |
| **API Gateway** | FastAPI + httpx (reverse proxy) | Centraliza auth y routing |

---

## 📁 Estructura del Repositorio

```
oneview-hospitality-platform/
├── 📂 hotel-service/          # Microservicio hotelero (FastAPI)
│   ├── app/
│   │   ├── main.py
│   │   ├── models.py          # SQLAlchemy ORM models
│   │   ├── schemas.py         # Pydantic schemas
│   │   ├── database.py
│   │   └── routers/
│   │       ├── kpis.py        # KPIs: ocupación, ADR, RevPAR
│   │       └── reservations.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── README.md
│
├── 📂 restaurant-service/     # Microservicio gastronómico (FastAPI)
│   ├── app/
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   └── routers/
│   │       ├── sales.py       # Ventas diarias por servicio
│   │       └── products.py    # Margen, rotación, top products
│   ├── Dockerfile
│   └── requirements.txt
│
├── 📂 realestate-service/     # Microservicio inmobiliario (FastAPI)
│   ├── app/
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   └── routers/
│   │       ├── funnel.py      # Funnel leads→visitas→contratos
│   │       └── units.py       # Estado de unidades
│   ├── Dockerfile
│   └── requirements.txt
│
├── 📂 analytics-service/      # ML/AI service (FastAPI + scikit-learn)
│   ├── app/
│   │   ├── main.py
│   │   ├── models/            # Trained ML models (.pkl)
│   │   └── routers/
│   │       ├── hotel_forecast.py
│   │       ├── restaurant_forecast.py
│   │       └── realestate_classifier.py
│   ├── notebooks/
│   │   ├── 01_hotel_forecasting.ipynb
│   │   ├── 02_restaurant_forecasting.ipynb
│   │   └── 03_realestate_classifier.ipynb
│   ├── Dockerfile
│   └── requirements.txt
│
├── 📂 chatbot-service/        # NLP chatbot sobre KPIs
│   ├── app/
│   │   └── main.py
│   └── Dockerfile
│
├── 📂 gateway-api/            # API Gateway unificado
│   ├── app/
│   │   └── main.py
│   └── Dockerfile
│
├── 📂 dashboard-ui/           # React SPA con dashboards ejecutivos
│   ├── src/
│   │   ├── pages/
│   │   │   ├── HotelDashboard.jsx
│   │   │   ├── RestaurantDashboard.jsx
│   │   │   └── RealEstateDashboard.jsx
│   │   └── components/
│   └── Dockerfile
│
├── 📂 data-loader/            # Scripts de generación y carga de datos
│   ├── generate_hotel_data.py
│   ├── generate_restaurant_data.py
│   ├── generate_realestate_data.py
│   ├── load_to_postgres.py
│   └── schema.sql
│
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 🚀 Inicio Rápido

### Prerrequisitos
- Docker Desktop ≥ 24.0
- Docker Compose ≥ 2.20
- Git

### 1. Clonar el repositorio
```bash
git clone https://github.com/aDavidBravo/oneview-hospitality-platform.git
cd oneview-hospitality-platform
```

### 2. Configurar variables de entorno
```bash
cp .env.example .env
# Editar .env si es necesario (los valores default funcionan en local)
```

### 3. Levantar toda la plataforma
```bash
docker-compose up --build
```

### 4. Cargar datos sintéticos (primera vez)
```bash
docker-compose exec data-loader python load_to_postgres.py
```

### 5. Acceder a los servicios

| Servicio | URL | Descripción |
|---|---|---|
| 🌐 **Dashboard UI** | http://localhost:3000 | React SPA con todos los dashboards |
| 🔀 **Gateway API** | http://localhost:8000 | Punto de entrada unificado |
| 🏨 **Hotel Service** | http://localhost:8001/docs | Swagger UI hotelero |
| 🍽️ **Restaurant Service** | http://localhost:8002/docs | Swagger UI gastronómico |
| 🏢 **Real Estate Service** | http://localhost:8003/docs | Swagger UI inmobiliario |
| 🤖 **Analytics Service** | http://localhost:8004/docs | Swagger UI ML/AI |
| 💬 **Chatbot** | http://localhost:8005 | Chatbot NLP |
| 🗄️ **PostgreSQL** | localhost:5432 | Base de datos (user: oneview) |

---

## 🤖 Modelos de IA / ML

### 1. Forecast de Ocupación Hotelera
- **Algoritmo**: Gradient Boosting Regressor + features de calendario
- **Inputs**: ocupación histórica, temporada, día de semana, eventos especiales
- **Output**: predicción 14 días adelante
- **Métricas**: RMSE ≈ 3.2%, MAE ≈ 2.8%
- **Endpoint**: `POST /analytics/predict/hotel-occupancy`

### 2. Forecast de Ventas del Restaurante
- **Algoritmo**: Random Forest + features temporales por servicio
- **Inputs**: ventas históricas por servicio (desayuno/almuerzo/cena), día semana
- **Output**: predicción ventas 14 días por servicio
- **Métricas**: RMSE ≈ $180 USD, MAE ≈ $140 USD
- **Endpoint**: `POST /analytics/predict/restaurant-sales`

### 3. Clasificador de Conversión Inmobiliaria
- **Algoritmo**: Logistic Regression + Gradient Boosting (ensemble)
- **Inputs**: características del lead (canal, visitas, tiempo en funnel, tipo unidad)
- **Output**: probabilidad de cierre 0-100%
- **Métricas**: AUC-ROC ≈ 0.84, Accuracy ≈ 78%
- **Endpoint**: `POST /analytics/predict/realestate-conversion`

---

## 📊 Dashboards Ejecutivos

### Panel Hotelero
- Ocupación actual vs. histórica (últimos 30 días)
- ADR (Average Daily Rate) y RevPAR en tiempo real
- Forecast de ocupación 14 días
- Heatmap de ocupación por tipo de habitación
- Breakdown de reservas por canal y país de origen

### Panel Gastronómico  
- Ventas diarias por servicio (área chart)
- Top 10 productos por ingresos y margen
- Mapa de calor de ventas por hora del día
- Forecast de ventas 14 días
- Alerta de stock / desperdicio estimado

### Panel Inmobiliario
- Funnel de conversión (leads → visitas → reservas → contratos)
- Estado de unidades por proyecto (disponibles/reservadas/vendidas)
- Ingresos acumulados y proyectados por mes
- Score de leads en tiempo real (ML)
- Análisis de pipeline por vendedor

---

## 💬 Chatbot de KPIs

El chatbot acepta preguntas en lenguaje natural como:

```
💬 "¿Cuál fue la ocupación promedio del hotel el último mes?"
🤖 → "La ocupación promedio del hotel en los últimos 30 días fue 73.4%, 
       comparado con 68.1% del mismo período del año anterior."

💬 "¿Cuántas unidades quedan disponibles en el proyecto norte?"
🤖 → "El proyecto norte tiene 12 unidades disponibles: 8 departamentos 
       de 2 dormitorios y 4 oficinas medianas."
```

---

## 🏗️ Despliegue en Nube (Referencia)

Esta arquitectura local puede llevarse a AWS/GCP con mínimos cambios:

```
Local Docker Compose → Producción Cloud
──────────────────────────────────────
PostgreSQL           → AWS RDS PostgreSQL (Multi-AZ)
Microservicios       → AWS ECS Fargate (o EKS)
Gateway API          → AWS API Gateway + ALB
Dashboard UI         → AWS CloudFront + S3
ML Models            → AWS SageMaker Endpoints
Secrets              → AWS Secrets Manager
Monitoreo            → CloudWatch + Grafana
```

---

## 📄 Licencia

MIT License — Proyecto de portafolio personal.

---

*Desarrollado como proyecto de portafolio para demostrar habilidades en arquitectura de microservicios, ingeniería de datos e IA aplicada a la industria hotelera y de real estate.*
