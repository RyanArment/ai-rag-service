"""
FastAPI application entry point.
"""
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import APP_NAME, APP_VERSION, DEBUG, LOG_LEVEL, LOG_JSON
from app.core.logging_config import setup_logging, get_logger
from app.core.exceptions import RAGServiceError
from app.routes import ask_router, documents_router, rag_router, sec_router

# Setup logging first
setup_logging(log_level=LOG_LEVEL, json_output=LOG_JSON)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info(f"Starting {APP_NAME} v{APP_VERSION}")
    yield
    # Shutdown
    logger.info(f"Shutting down {APP_NAME}")


# Create FastAPI app
app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    debug=DEBUG,
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add request ID to all requests for tracing."""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


# Exception handlers
@app.exception_handler(RAGServiceError)
async def rag_service_error_handler(request: Request, exc: RAGServiceError):
    """Handle custom RAG service errors."""
    logger.error(
        f"RAG service error: {exc.message}",
        extra={
            "request_id": getattr(request.state, "request_id", None),
            "status_code": exc.status_code,
            "details": exc.details,
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "message": exc.message,
                "details": exc.details,
            },
            "request_id": getattr(request.state, "request_id", None),
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    request_id = getattr(request.state, "request_id", None)
    logger.error(
        f"Unexpected error: {str(exc)}",
        exc_info=True,
        extra={"request_id": request_id}
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "message": "Internal server error",
                "details": {"error_type": type(exc).__name__} if DEBUG else {},
            },
            "request_id": request_id,
        }
    )


# Include routers
app.include_router(ask_router.router)
app.include_router(documents_router.router)
app.include_router(rag_router.router)
app.include_router(sec_router.router)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": APP_NAME,
        "version": APP_VERSION,
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": APP_NAME,
        "version": APP_VERSION,
        "docs": "/docs",
    }
