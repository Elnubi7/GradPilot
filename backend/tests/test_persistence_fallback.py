import os

import pytest

from app.core.config import settings
from app.schemas.advisor_schema import GeneratedProject
from app.services.project_service import ProjectService


def _build_generated_project() -> GeneratedProject:
    return GeneratedProject(
        id=1,
        title="AI Healthcare Assistant",
        category="AI",
        difficulty="medium",
        duration_months=5,
        tech_stack=["Flutter", "FastAPI", "Python"],
        description="A mobile AI healthcare assistant project.",
        problem="Students need a practical healthcare AI graduation project.",
        solution="Build a mobile app with FastAPI backend and AI assistant.",
        features=["Symptom input", "AI advice", "Dashboard"],
        evaluation_metrics=["response relevance", "latency", "user satisfaction"],
        paper_link="https://arxiv.org/abs/1234.5678",
        github_link="https://github.com/example/repo",
        feasibility_score=85,
        scope="5-month MVP project.",
        architecture_summary="Flutter frontend + FastAPI backend + AI service.",
        weekly_milestones=["Week 1: planning", "Week 2: backend", "Week 3: Flutter"],
        risks=["Scope creep", "API integration"],
        source_status="real_sources",
        source_titles=["Example Paper", "example/repo"],
        source_quality_score=80,
        paper_score=75,
        repository_score=85,
    )


def test_save_generated_project_prevents_duplicates_in_memory(monkeypatch):
    monkeypatch.setattr(settings, "enable_database", False)
    service = ProjectService()
    project = _build_generated_project()

    first = service.save_generated_project(project)
    second = service.save_generated_project(project)

    assert first.id == second.id
    assert len(service.get_all_projects()) == 1


@pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="Set TEST_DATABASE_URL to run database integration tests.",
)
def test_database_integration_placeholder():
    assert os.getenv("TEST_DATABASE_URL")
