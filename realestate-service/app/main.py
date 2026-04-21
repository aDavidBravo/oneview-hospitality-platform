from fastapi import FastAPI
from .routers import funnel, units, projects

app = FastAPI(
    title="OneView — Real Estate Service",
    description="Leads, funnel de ventas y unidades del complejo inmobiliario",
    version="1.0.0",
)

app.include_router(funnel.router,   prefix="/realestate/kpis",      tags=["KPIs"])
app.include_router(units.router,    prefix="/realestate/units",      tags=["Units"])
app.include_router(projects.router, prefix="/realestate/projects",   tags=["Projects"])

@app.get("/health")
def health():
    return {"status": "ok", "service": "realestate-service"}
