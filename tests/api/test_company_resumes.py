from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

import app.api.v1.routes.company_resumes as company_api
from app.modules.resume_builder.company_batch import CompanyResumeBatch, company_key
from tests.modules.resume_builder.test_company_batch import StubLLM, inputs


class StubCompiler:
    def compile(self, source: str, output_dir: Path) -> bytes:
        return b"%PDF-1.4 test company PDF"


def test_company_resume_routes_are_scoped_to_pipeline_run(tmp_path, monkeypatch):
    batch = CompanyResumeBatch(tmp_path, compiler=StubCompiler(), llm_router=StubLLM())
    resume, github, companies, matches = inputs()

    class FakeStore:
        def get_run(self, run_id):
            return {"config": {"output_dir": str(tmp_path)}} if run_id == "run-1" else None

        def get_artifact(self, run_id, name):
            return {"resume": resume, "github": github, "matches": matches}.get(name)

        def get_companies(self, run_id):
            return companies

    monkeypatch.setattr(company_api, "get_run_store", lambda: FakeStore())
    monkeypatch.setattr(company_api, "CompanyResumeBatch", lambda path: batch)
    app = FastAPI()
    app.include_router(company_api.router, prefix="/api/v1")
    client = TestClient(app)
    prefix = "/api/v1/resume-builder/runs/run-1/companies"

    generated = client.post(f"{prefix}/generate")
    assert generated.status_code == 200
    assert set(generated.json()) == {"Backend Co", "Vision Co"}
    assert client.get(prefix).json() == generated.json()
    backend_key = company_key("Backend Co")
    vision_key = company_key("Vision Co")
    backend = client.get(f"{prefix}/{backend_key}")
    assert backend.status_code == 200
    assert backend.json()["company_name"] == "Backend Co"
    assert client.get(f"{prefix}/{backend_key}/source").status_code == 200
    assert client.get(f"{prefix}/{backend_key}/pdf").content.startswith(b"%PDF-")

    edited_source = backend.json()["custom_latex"].replace("Demo Candidate", "Candidate Edited")
    response = client.put(f"{prefix}/{backend_key}", json={"custom_latex": edited_source})
    assert response.status_code == 200
    assert "Candidate Edited" in client.get(f"{prefix}/{backend_key}/source").text
    assert "Candidate Edited" not in client.get(f"{prefix}/{vision_key}/source").text

    assert client.get(f"{prefix}/unknown").status_code == 404
    assert client.get("/api/v1/resume-builder/runs/other/companies").status_code == 404
