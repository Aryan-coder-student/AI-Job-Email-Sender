from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.services.system_status import build_system_status

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/status")
def get_system_status() -> dict[str, object]:
    return build_system_status()
