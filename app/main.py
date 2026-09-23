import os
import logging
from typing import List
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.db.session import engine
from app.models.domain import Base
from app.core.config import settings
from app.core.envelope import error_response
from app.api import auth, scan, rules, users, audit, reports, dashboard

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("complyerg.main")

# Auto-migrate database tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Production-Grade Legal Metrology (2011) & Drugs and Cosmetics (1945) Compliance Engine",
    version="4.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ------------------------------------------------------------------------------
# Secure-by-Default CORS Configuration
# ------------------------------------------------------------------------------
# Enforce explicit origin whitelist from environment; strictly forbid wildcard '*'
cors_origins: List[str] = settings.cors_origins
logger.info(f"CORS initialized with restricted origins: {cors_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "X-Requested-With"],
)

# ------------------------------------------------------------------------------
# Static File Storage
# ------------------------------------------------------------------------------
os.makedirs(settings.STORAGE_DIR, exist_ok=True)
os.makedirs(os.path.join(settings.STORAGE_DIR, "images"), exist_ok=True)
os.makedirs(os.path.join(settings.STORAGE_DIR, "reports"), exist_ok=True)
app.mount("/storage", StaticFiles(directory=settings.STORAGE_DIR), name="storage")

# ------------------------------------------------------------------------------
# Standardized Error Envelopes
# ------------------------------------------------------------------------------
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        422: "VALIDATION_ERROR",
        500: "INTERNAL_SERVER_ERROR"
    }
    error_code = code_map.get(exc.status_code, "ERROR")
    return error_response(code=error_code, message=str(exc.detail), status_code=exc.status_code)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return error_response(code="VALIDATION_ERROR", message="Invalid request parameters", details=exc.errors(), status_code=422)

# ------------------------------------------------------------------------------
# Versioned Router Registration (/api/v1/*)
# ------------------------------------------------------------------------------
v1_prefix = settings.API_V1_STR
app.include_router(auth.router, prefix=v1_prefix)
app.include_router(scan.router, prefix=v1_prefix)
app.include_router(rules.router, prefix=v1_prefix)
app.include_router(users.router, prefix=v1_prefix)
app.include_router(audit.router, prefix=v1_prefix)
app.include_router(reports.router, prefix=v1_prefix)
app.include_router(dashboard.router, prefix=v1_prefix)

# Backward Compatibility Route Mounts
app.include_router(auth.router)
app.include_router(scan.router)
app.include_router(rules.router)
app.include_router(users.router)
app.include_router(audit.router)
app.include_router(reports.router)
app.include_router(dashboard.router)

@app.get("/")
def root():
    return {
        "system": settings.PROJECT_NAME,
        "status": "online",
        "version": "4.0.0",
        "api_v1": settings.API_V1_STR,
        "docs_url": "/docs"
    }

@app.get("/api/v1/health")
def health_check():
    """Comprehensive system health check endpoint."""
    from app.db.session import engine as _engine
    db_ok = False
    try:
        from sqlalchemy import text as _text
        with _engine.connect() as conn:
            conn.execute(_text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    from app.core.envelope import success_response
    return success_response({
        "status": "healthy" if db_ok else "degraded",
        "version": "4.0.0",
        "database": db_ok,
        "rules_seeded": True,
        "api_prefix": settings.API_V1_STR,
        "categories_supported": ["food", "medicine", "cosmetics", "imported"],
        "laws_covered": [
            "Legal Metrology (Packaged Commodities) Rules 2011",
            "Drugs and Cosmetics Rules 1945 (Schedule H/H1/X)"
        ]
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
