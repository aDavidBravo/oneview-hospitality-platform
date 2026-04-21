"""
Hotel Service - Main Application
OneView Hospitality Platform
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from .database import engine, Base
from .routers import kpis, reservations, rooms

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Hotel Service starting up...")
    yield
    logger.info("Hotel Service shutting down...")


app = FastAPI(
    title="OneView Hotel Service",
    description="""
    ## Hotel Domain Microservice
    
    Provides REST APIs for the 5-star hotel domain:
    - **KPIs**: Occupancy rate, ADR, RevPAR, revenue
    - **Reservations**: Query by date range, channel, country
    - **Rooms**: Availability and configuration
    
    Part of the **OneView Hospitality Platform**.
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(kpis.router, prefix="/hotel", tags=["KPIs"])
app.include_router(reservations.router, prefix="/hotel", tags=["Reservations"])
app.include_router(rooms.router, prefix="/hotel", tags=["Rooms"])


@app.get("/health", tags=["System"])
async def health_check():
    return {"status": "healthy", "service": "hotel-service", "version": "1.0.0"}


@app.get("/", tags=["System"])
async def root():
    return {
        "service": "OneView Hotel Service",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": [
            "/hotel/kpis/daily",
            "/hotel/kpis/monthly",
            "/hotel/kpis/summary",
            "/hotel/reservations",
            "/hotel/rooms",
        ]
    }
