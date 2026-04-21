"""
Gateway API - Unified entry point for all OneView services
Handles routing, CORS, and basic JWT authentication
"""
import os
import httpx
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

JWT_SECRET = os.getenv('JWT_SECRET', 'oneview_jwt_secret_change_in_prod')
JWT_ALGORITHM = 'HS256'

HOTEL_URL = os.getenv('HOTEL_SERVICE_URL', 'http://hotel-service:8001')
RESTAURANT_URL = os.getenv('RESTAURANT_SERVICE_URL', 'http://restaurant-service:8002')
REALESTATE_URL = os.getenv('REALESTATE_SERVICE_URL', 'http://realestate-service:8003')
ANALYTICS_URL = os.getenv('ANALYTICS_SERVICE_URL', 'http://analytics-service:8004')
CHATBOT_URL = os.getenv('CHATBOT_SERVICE_URL', 'http://chatbot-service:8005')

app = FastAPI(
    title="OneView API Gateway",
    description="""
    ## OneView Hospitality Platform - Unified API Gateway
    
    Single entry point for all microservices.
    
    ### Authentication
    Use `POST /auth/token` to get a JWT token, then include it as:
    `Authorization: Bearer <token>`
    
    ### Available Routes
    - `/hotel/**` -> Hotel Service (port 8001)
    - `/restaurant/**` -> Restaurant Service (port 8002)  
    - `/realestate/**` -> Real Estate Service (port 8003)
    - `/analytics/**` -> Analytics Service (port 8004)
    - `/chat/**` -> Chatbot Service (port 8005)
    """,
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv('ALLOWED_ORIGINS', 'http://localhost:3000').split(','),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer(auto_error=False)


# ==========================================
# Authentication
# ==========================================

FAKE_USERS = {
    "admin": {"password": "oneview2024", "role": "admin"},
    "director": {"password": "director2024", "role": "director"},
    "analyst": {"password": "analyst2024", "role": "analyst"},
}


@app.post("/auth/token", tags=["Authentication"])
async def get_token(username: str, password: str):
    """Get JWT access token. Demo users: admin/oneview2024, director/director2024"""
    user = FAKE_USERS.get(username)
    if not user or user['password'] != password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    payload = {
        "sub": username,
        "role": user['role'],
        "exp": datetime.utcnow() + timedelta(hours=8)
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return {"access_token": token, "token_type": "bearer", "role": user['role']}


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        return None  # Allow unauthenticated for dev
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


# ==========================================
# Reverse Proxy Helper
# ==========================================

async def proxy_request(request: Request, target_url: str):
    """Forward request to downstream service."""
    path = request.url.path
    query = request.url.query
    url = f"{target_url}{path}"
    if query:
        url += f"?{query}"
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            body = await request.body()
            headers = dict(request.headers)
            headers.pop('host', None)
            
            response = await client.request(
                method=request.method,
                url=url,
                headers=headers,
                content=body
            )
            return JSONResponse(
                content=response.json(),
                status_code=response.status_code
            )
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail=f"Service unavailable: {target_url}")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Gateway error: {str(e)}")


# ==========================================
# Route definitions
# ==========================================

@app.api_route("/hotel/{path:path}", methods=["GET", "POST", "PUT", "DELETE"], tags=["Hotel"])
async def hotel_proxy(request: Request, path: str):
    """Proxy to Hotel Service"""
    return await proxy_request(request, HOTEL_URL)


@app.api_route("/restaurant/{path:path}", methods=["GET", "POST", "PUT", "DELETE"], tags=["Restaurant"])
async def restaurant_proxy(request: Request, path: str):
    """Proxy to Restaurant Service"""
    return await proxy_request(request, RESTAURANT_URL)


@app.api_route("/realestate/{path:path}", methods=["GET", "POST", "PUT", "DELETE"], tags=["Real Estate"])
async def realestate_proxy(request: Request, path: str):
    """Proxy to Real Estate Service"""
    return await proxy_request(request, REALESTATE_URL)


@app.api_route("/analytics/{path:path}", methods=["GET", "POST", "PUT", "DELETE"], tags=["Analytics"])
async def analytics_proxy(request: Request, path: str):
    """Proxy to Analytics Service"""
    return await proxy_request(request, ANALYTICS_URL)


@app.api_route("/chat/{path:path}", methods=["GET", "POST"], tags=["Chatbot"])
async def chatbot_proxy(request: Request, path: str):
    """Proxy to Chatbot Service"""
    return await proxy_request(request, CHATBOT_URL)


@app.get("/health", tags=["System"])
async def health():
    """Gateway health + downstream services status"""
    services_status = {}
    for name, url in [
        ('hotel', HOTEL_URL),
        ('restaurant', RESTAURANT_URL),
        ('realestate', REALESTATE_URL),
        ('analytics', ANALYTICS_URL),
        ('chatbot', CHATBOT_URL),
    ]:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                r = await client.get(f"{url}/health")
                services_status[name] = "healthy" if r.status_code == 200 else "degraded"
        except:
            services_status[name] = "unreachable"
    
    return {
        "gateway": "healthy",
        "services": services_status,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/", tags=["System"])
async def root():
    return {
        "platform": "OneView Hospitality Platform",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }
