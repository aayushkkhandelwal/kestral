import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings
from app.core.logging import logger
from app.core.exceptions import (
    AppException,
    NotFoundException,
    UnauthorizedException,
    ForbiddenException,
    ConflictException,
    ValidationException,
    BusinessRuleException
)
from app.middleware.request_context import RequestContextMiddleware
from app.middleware.rate_limit import SimpleRateLimiterMiddleware
from app.api.v1.router import api_router
from app.database.session import engine, SessionLocal
from app.database.init import init_db

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Kestral AI Backend Enterprise Engine...")
    settings.init_storage_dirs()

    # Bootstrap default administrator account if needed
    try:
        with SessionLocal() as db:
            init_db(db)
    except Exception as e:
        logger.warning(f"Could not bootstrap database automatically on startup: {e}")

    yield

    # Shutdown
    logger.info("Shutting down Kestral AI Backend Engine...")
    engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Enterprise Forensic Evidence Management & Video Surveillance Platform",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request context and rate limiting
app.add_middleware(RequestContextMiddleware)
app.add_middleware(SimpleRateLimiterMiddleware, max_requests=120, window_seconds=60)

# Mount static asset folders for media access
app.mount("/faces", StaticFiles(directory=settings.FACES_DIR), name="faces")
app.mount("/frames", StaticFiles(directory=settings.FRAMES_DIR), name="frames")
app.mount("/exports", StaticFiles(directory=settings.EXPORTS_DIR), name="exports")
if os.path.exists(settings.RESULTS_DIR):
    app.mount("/results", StaticFiles(directory=settings.RESULTS_DIR), name="results")


# Exception Handlers
@app.exception_handler(NotFoundException)
async def not_found_handler(request: Request, exc: NotFoundException):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": exc.message, "error_code": exc.error_code}
    )


@app.exception_handler(UnauthorizedException)
async def unauthorized_handler(request: Request, exc: UnauthorizedException):
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": exc.message, "error_code": exc.error_code}
    )


@app.exception_handler(ForbiddenException)
async def forbidden_handler(request: Request, exc: ForbiddenException):
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"detail": exc.message, "error_code": exc.error_code}
    )


@app.exception_handler(ConflictException)
async def conflict_handler(request: Request, exc: ConflictException):
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": exc.message, "error_code": exc.error_code}
    )


@app.exception_handler(ValidationException)
async def validation_handler(request: Request, exc: ValidationException):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.message, "error_code": exc.error_code}
    )


@app.exception_handler(BusinessRuleException)
async def business_rule_handler(request: Request, exc: BusinessRuleException):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": exc.message, "error_code": exc.error_code}
    )


# Health check
@app.get("/health", tags=["Health"])
@app.get("/api/health", tags=["Health"])
@app.get(f"{settings.API_V1_PREFIX}/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "database": "configured"
    }


# Include V1 Routers
app.include_router(api_router, prefix=settings.API_V1_PREFIX)
