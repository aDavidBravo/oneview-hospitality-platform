from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .routers import sales, products

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(
    title="OneView Restaurant Service",
    description="""## Restaurant Domain Microservice
    
    Fine dining restaurant analytics:
    - **Sales**: Daily sales by service type (breakfast/lunch/dinner/bar/room_service)
    - **Products**: Top products, margin analysis, rotation
    """,
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

app.include_router(sales.router, prefix="/restaurant", tags=["Sales"])
app.include_router(products.router, prefix="/restaurant", tags=["Products"])

@app.get("/health")
async def health(): return {"status": "healthy", "service": "restaurant-service"}
