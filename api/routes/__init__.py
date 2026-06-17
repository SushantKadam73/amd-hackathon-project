"""GRC Platform - API Routes Package.

All API route modules are registered here and included in the main FastAPI app.
"""

from api.routes.frameworks import router as frameworks_router
from api.routes.evidence import router as evidence_router
from api.routes.reviews import router as reviews_router
from api.routes.audit import router as audit_router
from api.routes.reports import router as reports_router
from api.routes.users import router as users_router
from api.routes.agents import router as agents_router
from api.routes.rag import router as rag_router

__all__ = [
    "frameworks_router",
    "evidence_router",
    "reviews_router",
    "audit_router",
    "reports_router",
    "users_router",
    "agents_router",
    "rag_router",
]
