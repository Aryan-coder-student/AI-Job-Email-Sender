from app.api.v1.routes.pipeline import router as pipeline_router
from app.api.v1.routes.system import router as system_router

ROUTERS = (
    system_router,
    pipeline_router,
)

__all__ = ["ROUTERS"]
