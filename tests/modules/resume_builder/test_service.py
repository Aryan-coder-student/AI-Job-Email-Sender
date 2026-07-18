from pathlib import Path

import pytest

from app.modules.resume_builder.latex import LatexRenderer, validate_latex
from app.modules.resume_builder.matcher import KeywordRecommendationEngine
from app.modules.resume_builder.model import JobRequirements, ProfessionalProfile, ProfileItem, ResumeDocument
from app.modules.resume_builder.repository import JsonResumeBuilderRepository
from app.modules.resume_builder.service import ResumeBuilderService, profile_from_pipeline_artifact


class StubCompiler:
    def compile(self, source: str, output_dir: Path) -> bytes:
        return b"%PDF-test" if "\\begin{document}" in source else b""


@pytest.fixture
def profile() -> ProfessionalProfile:
    return ProfessionalProfile(
        name="Aryan & Co", summary="Backend engineer", skills=["Python", "FastAPI"],
        experiences=[ProfileItem(title="SDE Intern", description="Built FastAPI services", skills=["Python", "FastAPI"])],
        projects=[ProfileItem(title="Crawler", description="Playwright job crawler", skills=["Playwright", "Python"])],
        education=[ProfileItem(title="BTech CSE")],
    )


def test_recommendations_rank_job_overlap(profile):
    result = KeywordRecommendationEngine().recommend(
        profile, JobRequirements(company_name="Acme", role="Python backend engineer", required_skills=["FastAPI"]), 5,
    )
    assert result[0].title == "SDE Intern"
    assert result[0].score > result[1].score
    assert "fastapi" in result[0].matched_keywords


def test_renderer_escapes_profile_and_filters_items(profile):
    selected = profile.experiences[0].id
    source = LatexRenderer().render(ResumeDocument(company_name="Acme", profile=profile, selected_item_ids=[selected]))
    assert "Aryan \\& Co" in source
    assert "SDE Intern" in source
    assert "Crawler" not in source


def test_custom_latex_rejects_shell_and_file_commands():
    with pytest.raises(ValueError, match="forbidden"):
        validate_latex(r"\documentclass{article}\begin{document}\input{/etc/passwd}\end{document}")


def test_existing_latex_is_preserved_and_tailored(profile):
    source = r"\documentclass{article}\begin{document}\section*{Original}Keep this\end{document}"
    tailored = LatexRenderer().tailor_existing(
        source, company_name="Acme", role="Backend Engineer", projects=profile.projects,
        technical_keywords=["Python", "FastAPI"], nontechnical_keywords=["recruitment"],
    )
    assert r"\section*{Original}Keep this" in tailored
    assert "Acme" in tailored and "Crawler" in tailored
    assert tailored.count("RESUME-BUILDER:TAILORED-START") == 1


def test_pipeline_uses_ranked_github_projects_and_tags(tmp_path, profile):
    service = ResumeBuilderService(JsonResumeBuilderRepository(tmp_path), StubCompiler(), tmp_path)
    service.save_profile(profile)
    document = service.create_from_pipeline(
        source_latex=r"\documentclass{article}\begin{document}Base\end{document}",
        company={"company_name": "Acme", "role": "AI Engineer", "job_description": "Build APIs"},
        github={"projects": [{"repo_name": "Crawler", "summary": "Crawls job UIs", "repo_link": "https://github/x", "tech_stack": {"backend": ["Python"], "frontend": [], "ai_ml": ["LLM"]}, "non_tech_tags": ["recruitment"]}]},
        matches=[{"project_name": "Crawler", "final_score": 0.9}], limit=5,
    )
    assert "Crawler" in document.custom_latex
    assert "Python" in document.custom_latex
    assert "recruitment" in document.custom_latex


def test_service_persists_profile_and_document(tmp_path, profile):
    repository = JsonResumeBuilderRepository(tmp_path)
    service = ResumeBuilderService(repository, StubCompiler(), tmp_path / "compiled")
    service.save_profile(profile)
    document = service.create_document(JobRequirements(company_name="Acme", required_skills=["Python"]), "classic", 5)
    assert service.get_document(document.id) == document
    assert service.pdf(document) == b"%PDF-test"
    assert (tmp_path / "profile.json").exists()


def test_pipeline_artifact_maps_to_builder_profile():
    profile = profile_from_pipeline_artifact({
        "candidate_name": "Aryan", "skills": ["Python"],
        "projects": [{"project_name": "Crawler", "description": "BFS UI crawler"}],
        "links": {"emails": ["aryan@example.com"], "github": "https://github.com/aryan"},
    })
    assert profile.name == "Aryan"
    assert profile.projects[0].title == "Crawler"
    assert profile.email == "aryan@example.com"
