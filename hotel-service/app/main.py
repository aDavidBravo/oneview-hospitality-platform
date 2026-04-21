from fastapi import FastAPI
from .routers import kpis, reservations, rooms

app = FastAPI(
    title="OneView — Hotel Service",
    description="KPIs y reservas del hotel 5★",
    version="1.0.0",
)

app.include_router(kpis.router,         prefix="/hotel/kpis",         tags=["KPIs"])
app.include_router(reservations.router, prefix="/hotel/reservations",  tags=["Reservations"])
app.include_router(rooms.router,        prefix="/hotel/rooms",         tags=["Rooms"])

@app.get("/health")
def health():
    return {"status": "ok", "service": "hotel-service"}
