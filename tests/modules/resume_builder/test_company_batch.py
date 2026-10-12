import json

from pathlib import Path

import pytest

from app.modules.llm.interface import LLMResponse

from app.modules.resume_builder.company_batch import CompanyResumeBatch, company_key


class StubCompiler:
    def compile(self, source: str, output_dir: Path) -> bytes:
        assert r"\begin{document}" in source
        return b"%PDF-1.4 test result"



class StubLLM:
    """Test adapter, not a production relevance heuristic."""

    def __init__(self, response=None):
        self.calls = []
        self.response = response

    def generate(self, request):
        self.calls.append(request)
        marker = "Select company-relevant resume evidence from the JSON below.\n"
        evidence = json.loads(request.messages[1].content.split(marker, 1)[1].split("\n\nOutput schema:", 1)[0])
        project = evidence["eligible_projects"][0]
        experiences = evidence["candidate"]["experiences"]
        payload = self.response or {
            "projects": [{"item_id": project["id"], "score": 0.96, "reason": "Relevant factual GitHub project"}],
            "experiences": [
                {"item_id": item["id"], "score": 0.8, "reason": "Relevant verified work experience"}
                for item in experiences
            ],
            "skills": project["skills"][:1],
        }
        return LLMResponse(
            content=json.dumps(payload),
            provider="fixture-model-provider",
            model="fixture-model",
        )

def inputs():
    resume = {
        "candidate_name": "Demo Candidate",
        "skills": ["Python", "PyTorch", "FastAPI"],
        "experience": [{"company_name": "Demo Org", "description": "Built services"}],
        "education": ["BTech CS"],
        "links": {"emails": ["demo@example.com"]},
    }
    github = {"projects": [
        {"repo_name": "APIGateway", "summary": "FastAPI service", "repo_link": "https://github.com/example/api",
         "tech_stack": {"backend": ["FastAPI", "Python"], "frontend": [], "ai_ml": []}},
        {"repo_name": "ImageModel", "summary": "PyTorch image classifier", "repo_link": "https://github.com/example/ml",
         "tech_stack": {"backend": [], "frontend": [], "ai_ml": ["PyTorch"]}},
    ]}
    companies = [
        {"company_name": "Backend Co", "role": "Backend Engineer", "job_description": "FastAPI services"},
        {"company_name": "Vision Co", "role": "ML Engineer", "job_description": "PyTorch models"},
    ]
    matches = {
        "Backend Co": [{"project_name": "APIGateway", "final_score": 0.9}],
        "Vision Co": [{"project_name": "ImageModel", "final_score": 0.95}],
    }
    return resume, github, companies, matches


def test_company_matching_produces_isolated_resumes_and_index(tmp_path):
    llm = StubLLM()
    batch = CompanyResumeBatch(tmp_path, compiler=StubCompiler(), llm_router=llm)
    resume, github, companies, matches = inputs()
    entries = batch.generate(resume=resume, github=github, companies=companies, matches=matches)

    assert set(entries) == {"Backend Co", "Vision Co"}
    assert len(llm.calls) == 2
    assert all(entry["llm_model"] == "fixture-model" for entry in entries.values())
    assert entries["Backend Co"]["company_key"] != entries["Vision Co"]["company_key"]
    assert entries["Backend Co"]["document_id"] != entries["Vision Co"]["document_id"]
    assert batch.read_manifest() == entries
    backend = batch.service.get_document(entries["Backend Co"]["document_id"])
    vision = batch.service.get_document(entries["Vision Co"]["document_id"])
    assert backend is not None and vision is not None
    assert backend.company_name == "Backend Co"
    assert "APIGateway" in batch.service.latex(backend)
    assert "ImageModel" not in batch.service.latex(backend)
    assert "ImageModel" in batch.service.latex(vision)
    assert "APIGateway" not in batch.service.latex(vision)
    assert backend.profile.experiences == vision.profile.experiences
    assert batch.get_entry(company_key("Vision Co"))["company_name"] == "Vision Co"
    assert batch.get_entry("../other") is None


def test_missing_matches_do_not_create_unmatched_resume(tmp_path):
    batch = CompanyResumeBatch(tmp_path, compiler=StubCompiler(), llm_router=StubLLM())
    resume, github, companies, matches = inputs()
    matches["Vision Co"] = []
    assert set(batch.generate(resume=resume, github=github, companies=companies, matches=matches)) == {"Backend Co"}


def test_ranking_triggers_company_resume_generation(monkeypatch, tmp_path):
    from pipeline.context import PipelineContext
    from pipeline.config import PipelineOptions
    from pipeline.steps.handlers import RankProjectsStep

    captured = []
    class FakeBatch:
        def __init__(self, path):
            assert path == tmp_path
        def generate(self, **kwargs):
            captured.append(kwargs)

    class Artifact:
        def to_dict(self):
            return {"candidate_name": "Test Candidate", "projects": []}

    from pipeline import steps
    import pipeline.steps.handlers as handlers
    monkeypatch.setattr(handlers, "CompanyResumeBatch", FakeBatch)
    monkeypatch.setattr(handlers, "run_rank_applications", lambda **kwargs: [{"project_name": "APIGateway"}])

    context = PipelineContext(output_dir=tmp_path, candidate_id="candidate-1", companies=[{"company_name": "Backend Co"}])
    context.parsed_resume = Artifact()
    context.parsed_github = Artifact()
    RankProjectsStep().execute(context, PipelineOptions(output_dir=tmp_path))
    assert captured[0]["matches"]["Backend Co"][0]["project_name"] == "APIGateway"
    assert (tmp_path / "matches.json").is_file()


def test_jvs_template_handles_missing_optional_education_and_experience():
    from app.modules.resume_builder.latex import LatexRenderer
    from app.modules.resume_builder.model import ProfessionalProfile, ResumeDocument

    document = ResumeDocument(
        company_name="Acme",
        template="jvs",
        profile=ProfessionalProfile(name="New Graduate", skills=["Python"]),
    )
    source = LatexRenderer().render(document)
    assert r"\section{Education}" not in source
    assert r"\section{Experience}" not in source
    assert r"\begin{document}" in source
    assert r"\end{document}" in source


def test_llm_must_not_invent_skills_or_project_ids(tmp_path):
    resume, github, companies, matches = inputs()
    bogus_skills = StubLLM(response={
        "projects": [{"item_id": "nonexistent", "score": 0.8, "reason": "invalid reference"}],
        "experiences": [],
        "skills": ["ImaginaryFramework"],
    })
    batch = CompanyResumeBatch(tmp_path, compiler=StubCompiler(), llm_router=bogus_skills)
    with pytest.raises(ValueError, match="unknown or duplicate projects"):
        batch.generate(resume=resume, github=github, companies=companies[:1], matches=matches)
    assert not batch.manifest_path.exists()


def test_llm_rejects_skill_not_in_candidate_evidence(tmp_path):
    resume, github, companies, matches = inputs()
    from app.modules.resume_builder.llm_tailoring import project_reference
    bogus_skills = StubLLM(response={
        "projects": [{"item_id": project_reference("APIGateway"), "score": 0.8, "reason": "Backend relevant"}],
        "experiences": [],
        "skills": ["ImaginaryFramework"],
    })
    batch = CompanyResumeBatch(tmp_path, compiler=StubCompiler(), llm_router=bogus_skills)
    with pytest.raises(ValueError, match="unknown or duplicate skills"):
        batch.generate(resume=resume, github=github, companies=companies[:1], matches=matches)
    assert not batch.manifest_path.exists()


def test_llm_is_required_without_fallback(monkeypatch, tmp_path):
    resume, github, companies, matches = inputs()

    def no_llm():
        raise RuntimeError("No LLM provider configured")

    import app.modules.resume_builder.company_batch as module
    monkeypatch.setattr(module, "build_default_llm_router", no_llm)
    batch = CompanyResumeBatch(tmp_path, compiler=StubCompiler())
    with pytest.raises(RuntimeError, match="No LLM provider configured"):
        batch.generate(resume=resume, github=github, companies=companies[:1], matches=matches)
    assert not batch.manifest_path.exists()


def test_company_llm_prompt_uses_job_description_and_verified_evidence(tmp_path):
    resume, github, companies, matches = inputs()
    model = StubLLM()
    batch = CompanyResumeBatch(tmp_path, compiler=StubCompiler(), llm_router=model)
    batch.generate(resume=resume, github=github, companies=companies[:1], matches=matches)
    prompt = model.calls[0].messages[1].content
    assert "FastAPI services" in prompt
    assert "APIGateway" in prompt
    assert "Demo Org" in prompt
    assert "available_skills" in prompt
    assert "ImaginaryFramework" not in prompt
