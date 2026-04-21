from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import funnel, units

app = FastAPI(
    title="OneView Real Estate Service",
    description="""## Real Estate Domain Microservice
    
    - **Funnel**: Lead to contract conversion analytics
    - **Units**: Available, reserved and sold units by project
    """,
    version="1.0.0"
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(funnel.router, prefix="/realestate", tags=["Funnel"])
app.include_router(units.router, prefix="/realestate", tags=["Units"])

@app.get("/health")
async def health(): return {"status": "healthy", "service": "realestate-service"}
