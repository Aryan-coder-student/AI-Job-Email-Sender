from pathlib import Path

import pytest

from app.modules.resume_builder.latex import LatexRenderer, validate_latex
from app.modules.resume_builder.matcher import KeywordRecommendationEngine
from app.modules.resume_builder.model import JobRequirements, LatexUpdateRequest, ProfessionalProfile, ProfileItem, ResumeDocument
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


def test_jvs_is_default_self_contained_template(tmp_path, profile):
    service = ResumeBuilderService(JsonResumeBuilderRepository(tmp_path), StubCompiler(), tmp_path)
    service.save_profile(profile)
    document = service.create_document(JobRequirements(company_name="Acme", required_skills=["Python"]), "jvs", 5)
    assert "JV's Resume Template" in document.custom_latex
    assert r"\resumeProjectHeading" in document.custom_latex
    assert r"\input{particulars}" not in document.custom_latex


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


def test_toggle_recommendations_updates_custom_latex(tmp_path):
    project1 = ProfileItem(title="Project Alpha", description="Alpha project description", skills=["Python"])
    project2 = ProfileItem(title="Project Beta", description="Beta project description", skills=["FastAPI"])
    custom_profile = ProfessionalProfile(
        name="Candidate", headline="Dev", email="c@example.com",
        projects=[project1, project2],
    )
    service = ResumeBuilderService(JsonResumeBuilderRepository(tmp_path), StubCompiler(), tmp_path / "compiled")
    service.save_profile(custom_profile)

    doc = service.create_document(JobRequirements(company_name="Acme", role="Backend Engineer", required_skills=["Python", "FastAPI"]), "jvs", 5)
    # Both projects are initially recommended and selected
    assert "Project Alpha" in doc.custom_latex
    assert "Project Beta" in doc.custom_latex

    # Deselect Project Beta
    updated = service.update_document(doc, LatexUpdateRequest(selected_item_ids=[project1.id], custom_latex=None))
    assert "Project Alpha" in updated.custom_latex
    assert "Project Beta" not in updated.custom_latex

    # Deselect all
    updated_none = service.update_document(updated, LatexUpdateRequest(selected_item_ids=[], custom_latex=None))
    assert "Project Alpha" not in updated_none.custom_latex
    assert "Project Beta" not in updated_none.custom_latex

    # Re-select Project Beta only
    updated_beta = service.update_document(updated_none, LatexUpdateRequest(selected_item_ids=[project2.id], custom_latex=None))
    assert "Project Alpha" not in updated_beta.custom_latex
    assert "Project Beta" in updated_beta.custom_latex


def test_complete_resume_builder_flow(tmp_path):
    # Step 1: Import profile
    raw_artifact = {
        "candidate_name": "Taylor Swift",
        "summary": "Experienced distributed systems developer.",
        "skills": ["Go", "Kubernetes", "PostgreSQL"],
        "experience": [{"company_name": "CloudCo", "description": "Engineered high-throughput event queues"}],
        "projects": [{"project_name": "MeshNet", "description": "Service mesh in Go", "technologies": ["Go"]}],
        "links": {"emails": ["taylor@example.com"], "github": "https://github.com/taylor"},
    }
    imported_profile = profile_from_pipeline_artifact(raw_artifact)
    service = ResumeBuilderService(JsonResumeBuilderRepository(tmp_path), StubCompiler(), tmp_path / "compiled")
    saved_profile = service.save_profile(imported_profile)
    assert saved_profile.name == "Taylor Swift"

    # Step 2: Select job & Step 3: Generate resume
    job = JobRequirements(
        company_name="Infrastructure Inc",
        role="Systems Engineer",
        description="Looking for Go and Kubernetes engineers",
        required_skills=["Go", "Kubernetes"],
    )
    doc = service.create_document(job, template="jvs", limit=5)
    assert doc.company_name == "Infrastructure Inc"
    assert "Taylor Swift" in doc.custom_latex
    assert "MeshNet" in doc.custom_latex

    # Step 4: Edit LaTeX & Step 5: Save
    modified_latex = doc.custom_latex.replace("Taylor Swift", "Taylor Swift, Lead Engineer")
    saved_doc = service.update_document(doc, LatexUpdateRequest(custom_latex=modified_latex))
    assert "Taylor Swift, Lead Engineer" in saved_doc.custom_latex

    # Step 6: Preview (LaTeX source & PDF compilation)
    source = service.latex(saved_doc)
    assert "Taylor Swift, Lead Engineer" in source
    pdf_bytes = service.pdf(saved_doc)
    assert pdf_bytes.startswith(b"%PDF-")

    # Step 7: Download / Export verification
    reloaded_doc = service.get_document(saved_doc.id)
    assert reloaded_doc is not None
    assert service.latex(reloaded_doc) == modified_latex

