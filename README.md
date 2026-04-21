# 🏨 OneView Hospitality Platform

> **Analítica, Microservicios e IA para un holding de Hotelería 5★, Gastronomía y Real Estate**

[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue)](https://postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED)](https://docker.com)
[![Scikit-learn](https://img.shields.io/badge/Scikit--learn-1.4-orange)](https://scikit-learn.org)

---

## 📋 Descripción del Proyecto

**OneView** es una plataforma de analítica e inteligencia artificial diseñada para un holding empresarial que opera tres unidades de negocio integradas:

| Unidad | Descripción |
|--------|-------------|
| 🏨 **Hotel 5★** | Gestión de ocupación, reservas, tarifas ADR/RevPAR |
| 🍽️ **Restaurante Fine Dining** | Ventas por servicio, márgenes, inventario y forecasting |
| 🏢 **Complejo Inmobiliario** | Funnel de leads, estado de unidades e ingresos proyectados |

Este proyecto demuestra de manera integrada: arquitectura de microservicios, ingeniería de datos, modelos de IA/ML aplicados al negocio, y dashboards ejecutivos de Business Intelligence.

---

## 🏗️ Arquitectura de Microservicios

```
┌─────────────────────────────────────────────────────────────┐
│                    ONEVIEW PLATFORM                          │
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │ hotel-service│    │restaurant-   │    │ realestate-  │  │
│  │  :8001       │    │  service     │    │  service     │  │
│  │  FastAPI     │    │  :8002       │    │  :8003       │  │
│  │  Python      │    │  FastAPI     │    │  FastAPI     │  │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘  │
│         │                   │                    │          │
│  ┌──────▼───────────────────▼────────────────────▼───────┐  │
│  │              analytics-service  :8004                 │  │
│  │         (ML Models / Forecasting / AI Engine)         │  │
│  └──────────────────────────┬────────────────────────────┘  │
│                              │                              │
│  ┌───────────────────────────▼────────────────────────────┐ │
│  │              gateway-api  :8000                        │ │
│  │     (Nginx reverse proxy + Auth + Rate limiting)       │ │
│  └───────────────────────────┬────────────────────────────┘ │
│                              │                              │
│  ┌───────────────────────────▼────────────────────────────┐ │
│  │              PostgreSQL  :5432                         │ │
│  │   Schemas: hotel | restaurant | realestate | analytics │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌────────────────┐  ┌──────────────┐  ┌───────────────┐   │
│  │  dashboard-ui  │  │  chatbot     │  │  data-loader  │   │
│  │  :3000 (HTML)  │  │  :8005       │  │  (ETL/seeder) │   │
│  └────────────────┘  └──────────────┘  └───────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Inicio Rápido

### Pre-requisitos
- Docker 24+ y Docker Compose v2
- Git

### Levantar el entorno completo

```bash
# 1. Clonar el repositorio
git clone https://github.com/aDavidBravo/oneview-hospitality-platform.git
cd oneview-hospitality-platform

# 2. Copiar variables de entorno
cp .env.example .env

# 3. Levantar todos los servicios
docker-compose up --build

# 4. (Opcional) Cargar datos sintéticos de 24 meses
docker-compose exec data-loader python generate_all.py
```

Accede a:
- 🌐 **Dashboard UI**: http://localhost:3000
- 🔀 **API Gateway**: http://localhost:8000
- 📚 **Docs Hotel**: http://localhost:8001/docs
- 📚 **Docs Restaurant**: http://localhost:8002/docs
- 📚 **Docs Real Estate**: http://localhost:8003/docs
- 📚 **Docs Analytics**: http://localhost:8004/docs
- 🤖 **Chatbot**: http://localhost:8005

---

## 🛠️ Stack Tecnológico

| Capa | Tecnología | Justificación |
|------|-----------|---------------|
| **Backend** | Python 3.11 + FastAPI | Alto rendimiento, tipado, autodocs OpenAPI |
| **Base de datos** | PostgreSQL 15 | ACID, jsonb, ventanas analíticas, escalable |
| **ORM** | SQLAlchemy 2.0 | Migrations + Query builder tipado |
| **ML/AI** | scikit-learn, statsmodels, Prophet | Estándar industria para forecasting y clasificación |
| **Visualización** | Plotly + Chart.js | Gráficos interactivos sin dependencias externas |
| **Infraestructura** | Docker Compose + Nginx | Orquestación local lista para migrar a ECS/K8s |
| **Datos sintéticos** | Faker + pandas + numpy | Simulación realista con estacionalidad |

---

## 📊 Modelos de IA Implementados

| Modelo | Dominio | Algoritmo | Métrica |
|--------|---------|-----------|--------|
| **Forecast Ocupación** | Hotel | Prophet + SARIMA | RMSE < 3% |
| **Forecast Ventas** | Restaurante | Linear Regression + Seasonal | MAE < 8% |
| **Conversión de Leads** | Inmobiliaria | Random Forest Classifier | ROC-AUC > 0.85 |

---

## 📁 Estructura del Proyecto

```
oneview-hospitality-platform/
├── 📄 README.md
├── 📄 docker-compose.yml
├── 📄 .env.example
├── 📄 nginx.conf
│
├── 🏨 hotel-service/
│   ├── app/ (FastAPI app)
│   ├── Dockerfile
│   └── README.md
│
├── 🍽️ restaurant-service/
│   ├── app/ (FastAPI app)
│   ├── Dockerfile
│   └── README.md
│
├── 🏢 realestate-service/
│   ├── app/ (FastAPI app)
│   ├── Dockerfile
│   └── README.md
│
├── 🤖 analytics-service/
│   ├── app/ (FastAPI + ML models)
│   ├── models/ (trained .pkl files)
│   ├── notebooks/
│   ├── Dockerfile
│   └── README.md
│
├── 🔀 gateway-api/
│   ├── nginx.conf
│   └── Dockerfile
│
├── 💬 chatbot-service/
│   ├── app/
│   ├── Dockerfile
│   └── README.md
│
├── 📊 dashboard-ui/
│   ├── index.html
│   ├── hotel.html
│   ├── restaurant.html
│   └── realestate.html
│
├── 🗄️ data-loader/
│   ├── generate_hotel.py
│   ├── generate_restaurant.py
│   ├── generate_realestate.py
│   ├── generate_all.py
│   ├── schema.sql
│   └── Dockerfile
│
└── 📓 notebooks/
    ├── 01_hotel_eda_forecast.ipynb
    ├── 02_restaurant_eda_forecast.ipynb
    └── 03_realestate_lead_scoring.ipynb
```

---

## 🌩️ Migración a Cloud (AWS)

Esta arquitectura está diseñada para migrar fácilmente a AWS:

```
Local Docker        →  AWS Equivalente
─────────────────────────────────────────
PostgreSQL          →  RDS PostgreSQL
FastAPI containers  →  ECS Fargate / EKS
Nginx gateway       →  AWS API Gateway
HTML Dashboard      →  S3 + CloudFront
Modelos ML          →  SageMaker
ETL scripts         →  AWS Glue / Lambda
```

---

## 👤 Autor

Proyecto de portafolio desarrollado como demostración de habilidades en:
- Arquitectura de microservicios e infraestructura
- Ingeniería de datos y Business Intelligence  
- IA aplicada a decisiones de negocio en hotelería, gastronomía e inmobiliaria
- Desarrollo full-stack con Python y Docker

---

*OneView Hospitality Platform — Portfolio Project*
