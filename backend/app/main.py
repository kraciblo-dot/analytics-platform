from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

# Models must be imported for Alembic to read them
from app.db.database import engine, Base
import app.models.tenant 
import app.models.event

from app.api.routers import auth, events, analytics, websockets, dashboards
from app.core.limiter import limiter

app = FastAPI(
    title="Analytics Platform API",
    description="Real-Time Analytics & Reporting Platform",
    version="1.0.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(events.router)
app.include_router(analytics.router)
app.include_router(websockets.router)
app.include_router(dashboards.router)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "analytics-api"}