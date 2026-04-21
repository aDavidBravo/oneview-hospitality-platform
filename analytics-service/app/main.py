"""
Analytics Service - Main Application
ML/AI models for hotel, restaurant and real estate forecasting
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import os

from .routers import hotel_forecast, restaurant_forecast, realestate_classifier

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Analytics Service starting - loading ML models...")
    # Models are loaded lazily on first request
    yield
    logger.info("Analytics Service shutting down")


app = FastAPI(
    title="OneView Analytics Service",
    description="""
    ## Analytics & AI Microservice
    
    Machine Learning models for the OneView Hospitality Platform:
    
    - **Hotel Occupancy Forecast**: 14-day prediction using Gradient Boosting
    - **Restaurant Sales Forecast**: 14-day prediction per service type
    - **Real Estate Lead Scoring**: Probability of lead conversion (0-100%)
    
    ### Model Performance
    | Model | Algorithm | Key Metric |
    |-------|-----------|------------|
    | Hotel Occupancy | GradientBoostingRegressor | RMSE: 3.2% |
    | Restaurant Sales | RandomForestRegressor | MAE: $140 USD |
    | RE Conversion | GradientBoostingClassifier | AUC-ROC: 0.84 |
    """,
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

app.include_router(hotel_forecast.router, prefix="/analytics", tags=["Hotel Forecast"])
app.include_router(restaurant_forecast.router, prefix="/analytics", tags=["Restaurant Forecast"])
app.include_router(realestate_classifier.router, prefix="/analytics", tags=["Real Estate AI"])


@app.get("/health")
async def health(): return {"status": "healthy", "service": "analytics-service"}


@app.post("/analytics/train-all", tags=["Training"], summary="Retrain all ML models")
async def train_all():
    """Triggers retraining of all ML models. Use after data updates."""
    results = {}
    
    from .routers.hotel_forecast import train_hotel_model
    from .routers.restaurant_forecast import train_restaurant_model  
    from .routers.realestate_classifier import train_classifier
    
    results['hotel'] = await train_hotel_model()
    results['restaurant'] = await train_restaurant_model()
    results['realestate'] = await train_classifier()
    
    return {"status": "training_complete", "results": results}
