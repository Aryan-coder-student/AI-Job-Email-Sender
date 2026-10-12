from pathlib import Path

from app.modules.resume_builder.company_batch import CompanyResumeBatch, company_key


class StubCompiler:
    def compile(self, source: str, output_dir: Path) -> bytes:
        assert r"\begin{document}" in source
        return b"%PDF-1.4 test result"


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
    batch = CompanyResumeBatch(tmp_path, compiler=StubCompiler())
    resume, github, companies, matches = inputs()
    entries = batch.generate(resume=resume, github=github, companies=companies, matches=matches)

    assert set(entries) == {"Backend Co", "Vision Co"}
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
    batch = CompanyResumeBatch(tmp_path, compiler=StubCompiler())
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
