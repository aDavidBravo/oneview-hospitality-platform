from fastapi import FastAPI
from .routers import kpis, products

app = FastAPI(
    title="OneView — Restaurant Service",
    description="Ventas, márgenes y KPIs del restaurante fine dining",
    version="1.0.0",
)

app.include_router(kpis.router,      prefix="/restaurant/kpis",     tags=["KPIs"])
app.include_router(products.router,  prefix="/restaurant/products",  tags=["Products"])

@app.get("/health")
def health():
    return {"status": "ok", "service": "restaurant-service"}
