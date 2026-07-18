from app.api.v1.routes.pipeline import router as pipeline_router
from app.api.v1.routes.resume_builder import router as resume_builder_router
from app.api.v1.routes.system import router as system_router

ROUTERS = (
    system_router,
    pipeline_router,
    resume_builder_router,
)

__all__ = ["ROUTERS"]
