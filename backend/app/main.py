from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from starlette.middleware.base import BaseHTTPMiddleware
import structlog
import uuid

from app.db.database import engine, Base
import app.models.tenant 
import app.models.event

from app.api.routers import auth, events, analytics, websockets, dashboards, api_keys, invites
from app.core.limiter import limiter

structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)
logger = structlog.get_logger()

app = FastAPI(
    title="Analytics Platform API",
    description="Real-Time Analytics & Reporting Platform",
    version="1.0.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://analytics-platform-ten.vercel.app",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RequestTracingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        correlation_id = str(uuid.uuid4())
        structlog.contextvars.bind_contextvars(correlation_id=correlation_id)
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        
        structlog.contextvars.clear_contextvars()
        return response

app.add_middleware(RequestTracingMiddleware)

app.include_router(auth.router)
app.include_router(events.router)
app.include_router(analytics.router)
app.include_router(websockets.router)
app.include_router(dashboards.router)
app.include_router(api_keys.router)
app.include_router(invites.router)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "analytics-api"}