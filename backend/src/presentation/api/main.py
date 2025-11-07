from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from presentation.api.routes.health import router as health_router
from presentation.api.routes.webhook import router as webhook_router
from presentation.api.routes.cases import router as cases_router
from presentation.api.routes.metrics import router as metrics_router
from presentation.api.routes.auth import router as auth_router
from presentation.api.routes.users import router as users_router
from presentation.api.middleware.rate_limit import (
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
    RequestLoggingMiddleware
)
from infrastructure.persistence.db import init_db
import structlog

logger = structlog.get_logger()

app = FastAPI(
    title="Defensoría Civil - LLM Intelligence System",
    version="0.1.0",
    description="Sistema de asistencia legal automatizada para divorcios",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS para permitir frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middlewares de seguridad y logging
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware)

@app.on_event("startup")
def on_startup():
    init_db()

app.include_router(health_router, prefix="/health", tags=["health"])
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(webhook_router, prefix="/webhook", tags=["webhook"])
app.include_router(cases_router, prefix="/api/cases", tags=["cases"])
app.include_router(metrics_router, prefix="/api/metrics", tags=["metrics"])
app.include_router(users_router, prefix="/api/users", tags=["users"])
