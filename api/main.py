"""GRC Platform MVP - FastAPI Backend Entry Point.

Run with:
    uvicorn api.main:app --reload --port 8000
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_config
from api.routes import (
    agents_router,
    audit_router,
    evidence_router,
    frameworks_router,
    rag_router,
    reports_router,
    reviews_router,
    users_router,
)

config = get_config()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler.

    Manages startup and shutdown lifecycle events.
    Currently handles connection pool cleanup on shutdown.
    """
    yield
    # Shutdown: clean up database connection pool
    from api.database import close_pool
    close_pool()


app = FastAPI(
    title="GRC Platform API",
    description="Governance, Risk, and Compliance Platform Backend",
    version="0.1.0",
    debug=config.debug,
    lifespan=lifespan,
)

# Configure CORS for Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API route modules
app.include_router(agents_router)
app.include_router(frameworks_router)
app.include_router(evidence_router)
app.include_router(reviews_router)
app.include_router(audit_router)
app.include_router(reports_router)
app.include_router(users_router)
app.include_router(rag_router)


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "environment": config.env,
        "llm_provider": config.llm.provider,
    }


@app.get("/api/v1/status")
async def api_status() -> dict:
    """API status endpoint returning current configuration state."""
    return {
        "status": "running",
        "version": "0.1.0",
        "environment": config.env,
        "llm": {
            "provider": config.llm.provider,
            "model": config.llm.model,
        },
        "embedding": {
            "provider": config.embedding.provider,
            "model": config.embedding.model,
            "dimensions": config.embedding.dimensions,
        },
        "features": {
            "ai_chat": config.enable_ai_chat,
            "auto_mapping": config.enable_auto_mapping,
            "mock_data": config.enable_mock_data,
        },
    }
