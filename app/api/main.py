from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.routes import ROUTERS

API_PREFIX = "/api/v1"


def create_app() -> FastAPI:
    app = FastAPI(title="Job Send Crawl API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    include_api_routes(app)

    return app


def include_api_routes(app: FastAPI) -> None:
    for router in ROUTERS:
        app.include_router(router, prefix=API_PREFIX)


app = create_app()
