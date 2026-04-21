from fastapi import FastAPI
from .routers import hotel_ml, restaurant_ml, realestate_ml, training

app = FastAPI(
    title="OneView — Analytics & AI Service",
    description="Forecasting, ML models e inteligencia de negocios",
    version="1.0.0",
)

app.include_router(hotel_ml.router,      prefix="/analytics/predict",  tags=["Hotel AI"])
app.include_router(restaurant_ml.router, prefix="/analytics/predict",  tags=["Restaurant AI"])
app.include_router(realestate_ml.router, prefix="/analytics/predict",  tags=["RealEstate AI"])
app.include_router(training.router,      prefix="/analytics/train",    tags=["Training"])

@app.get("/health")
def health():
    return {"status": "ok", "service": "analytics-service"}
