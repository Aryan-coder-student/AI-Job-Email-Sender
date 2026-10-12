from pathlib import Path

from fastapi.testclient import TestClient

from fastapi import FastAPI

from app.api.v1.routes.resume_builder import get_service, router
from app.modules.resume_builder.repository import JsonResumeBuilderRepository
from app.modules.resume_builder.service import ResumeBuilderService
from tests.modules.resume_builder.test_company_batch import StubLLM


class StubCompiler:
    def compile(self, source: str, output_dir: Path) -> bytes:
        return b"%PDF-1.4"


def test_resume_builder_flow(tmp_path):
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    app.dependency_overrides[get_service] = lambda: ResumeBuilderService(
        JsonResumeBuilderRepository(tmp_path), StubCompiler(), tmp_path / "compiled", llm_router=StubLLM()
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

def test_manual_resume_requires_llm_and_returns_explicit_unavailable_error(tmp_path, monkeypatch):
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    import app.modules.llm.factory as factory

    def missing_provider():
        raise RuntimeError("No LLM provider configured")

    monkeypatch.setattr(factory, "build_default_llm_router", missing_provider)
    service = ResumeBuilderService(JsonResumeBuilderRepository(tmp_path), StubCompiler(), tmp_path)
    app.dependency_overrides[get_service] = lambda: service
    client = TestClient(app)
    client.put("/api/v1/resume-builder/profile", json={"name": "Candidate", "skills": ["Python"]})
    response = client.post(
        "/api/v1/resume-builder/documents",
        json={"job": {"company_name": "Acme", "role": "Backend Engineer"}, "recommendation_limit": 5},
    )
    assert response.status_code == 503
    assert "No LLM provider configured" in response.json()["detail"]
    recommended = client.post(
        "/api/v1/resume-builder/recommendations",
        json={"job": {"company_name": "Acme", "role": "Backend Engineer"}, "limit": 5},
    )
    assert recommended.status_code == 503
