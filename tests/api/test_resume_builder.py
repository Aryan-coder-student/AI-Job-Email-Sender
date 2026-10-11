from pathlib import Path

from fastapi.testclient import TestClient

from fastapi import FastAPI

from app.api.v1.routes.resume_builder import get_service, router
from app.modules.resume_builder.repository import JsonResumeBuilderRepository
from app.modules.resume_builder.service import ResumeBuilderService


class StubCompiler:
    def compile(self, source: str, output_dir: Path) -> bytes:
        return b"%PDF-1.4"


def test_resume_builder_flow(tmp_path):
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    app.dependency_overrides[get_service] = lambda: ResumeBuilderService(
        JsonResumeBuilderRepository(tmp_path), StubCompiler(), tmp_path / "compiled"
    )
    client = TestClient(app)
    profile = {
        "name": "Test User", "skills": ["Python"],
        "projects": [{"title": "API", "description": "FastAPI backend", "skills": ["Python", "FastAPI"]}],
    }
    assert client.put("/api/v1/resume-builder/profile", json=profile).status_code == 200
    response = client.post("/api/v1/resume-builder/documents", json={
        "job": {"company_name": "Acme", "role": "Backend", "required_skills": ["FastAPI"]},
        "recommendation_limit": 5,
    })
    assert response.status_code == 200
    document_id = response.json()["id"]
    source = client.get(f"/api/v1/resume-builder/documents/{document_id}/source")
    assert source.status_code == 200
    assert "Test User" in source.text
