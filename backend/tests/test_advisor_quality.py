from app.core.config import settings
from app.schemas.advisor_schema import (
    AdvisorChatRequest,
    AdvisorProjectGenerationRequest,
    GeneratedProject,
    ProjectChatMessage,
)
from app.schemas.source_schema import SourcePaper, SourceRepository, SourceSearchResponse
from app.services.advisor_service import ENGLISH_SCOPE_REMINDER, advisor_service
from app.services.github_service import github_service


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


def _build_source_paper() -> SourcePaper:
    return SourcePaper(
        title="Privacy-preserving machine learning for healthcare triage",
        summary="A paper about privacy-aware healthcare triage and safe AI decision support.",
        authors=["A. Researcher"],
        published="2025-01-01",
        link="https://arxiv.org/abs/1234.5678",
    )


def _build_referral_source_paper() -> SourcePaper:
    return SourcePaper(
        title="Clinical referral understanding with large language models",
        summary="A healthcare paper focused on referral document analysis, doctor routing, and evidence extraction.",
        authors=["B. Researcher"],
        published="2025-03-10",
        link="https://arxiv.org/abs/2345.6789",
    )


def _build_lifecycle_source_paper() -> SourcePaper:
    return SourcePaper(
        title="Monitoring clinical AI lifecycle performance in hospitals",
        summary="A paper about lifecycle monitoring, drift analytics, and dashboard visibility for healthcare AI systems.",
        authors=["C. Researcher"],
        published="2024-11-20",
        link="https://arxiv.org/abs/3456.7890",
    )


def _build_weak_healthcare_paper() -> SourcePaper:
    return SourcePaper(
        title="Competing Visions of Ethical AI",
        summary="A broad discussion of AI governance, incentives, and public framing without any domain-specific application workflow.",
        authors=["D. Researcher"],
        published="2025-02-14",
        link="https://arxiv.org/abs/4567.8901",
    )


def _build_agriculture_source_paper() -> SourcePaper:
    return SourcePaper(
        title="Coverage path planning and crop monitoring for precision agriculture",
        summary=(
            "A paper about field mission planning, crop monitoring, irrigation support, "
            "and practical farm supervisor reporting."
        ),
        authors=["E. Researcher"],
        published="2025-04-09",
        link="https://arxiv.org/abs/5678.9012",
    )


def _build_agriculture_repository() -> SourceRepository:
    return SourceRepository(
        name="precision-farm-dashboard",
        full_name="agriteam/precision-farm-dashboard",
        description=(
            "FastAPI backend and dashboard for crop monitoring, irrigation planning, "
            "and farm operations reporting."
        ),
        stars=145,
        language="Python",
        url="https://github.com/agriteam/precision-farm-dashboard",
    )


def _build_source_repository() -> SourceRepository:
    return SourceRepository(
        name="referral-assistant",
        full_name="openhealth/referral-assistant",
        description=(
            "Flutter and FastAPI healthcare assistant for referral analysis "
            "and doctor dashboard."
        ),
        stars=240,
        language="Python",
        url="https://github.com/openhealth/referral-assistant",
    )


def _build_lifecycle_repository() -> SourceRepository:
    return SourceRepository(
        name="clinical-ai-monitor",
        full_name="medops/clinical-ai-monitor",
        description=(
            "Flutter dashboard and FastAPI backend for monitoring clinical AI models, "
            "drift analytics, and doctor-facing alerts."
        ),
        stars=190,
        language="Dart",
        url="https://github.com/medops/clinical-ai-monitor",
    )


def _merge_prompt(prompt_text: str):
    request = AdvisorProjectGenerationRequest(prompt_text=prompt_text, max_results=5)
    parsed = advisor_service._parse_prompt_preferences(request)
    return advisor_service._merge_preferences(request, parsed)


def test_arabic_mixed_prompt_parsing_detects_ai_healthcare_and_stack():
    preferences = _merge_prompt(
        "عايز ML healthcare mobile app بالـ فلاتر و fast api و بايثون في 5 شهور"
    )

    assert "AI" in preferences.interests
    assert "Healthcare" in preferences.interests
    assert "Flutter" in preferences.preferred_stack
    assert "FastAPI" in preferences.preferred_stack
    assert "Python" in preferences.preferred_stack
    assert preferences.project_type == "mobile app"
    assert preferences.duration_months == 5


def test_team_size_parsing_detects_three_members():
    preferences = _merge_prompt("احنا 3 في التيم وعايزين AI healthcare app")

    assert preferences.team_size == 3


def test_swagger_placeholder_values_do_not_override_prompt_preferences():
    request = AdvisorProjectGenerationRequest(
        interests=["string"],
        level="string",
        duration_months=1,
        preferred_stack=["string"],
        project_type="product",
        prompt_text=(
            "احنا 3 في التيم وعايزين AI healthcare mobile app باستخدام Flutter "
            "و FastAPI و Python ويتعمل في 5 شهور"
        ),
        max_results=5,
    )

    parsed = advisor_service._parse_prompt_preferences(request)
    preferences = advisor_service._merge_preferences(request, parsed)

    assert "AI" in preferences.interests
    assert "Healthcare" in preferences.interests
    assert "Flutter" in preferences.preferred_stack
    assert "FastAPI" in preferences.preferred_stack
    assert "Python" in preferences.preferred_stack
    assert preferences.project_type == "mobile app"
    assert preferences.duration_months == 5
    assert preferences.team_size == 3


def test_generated_projects_preserve_requested_stack_order():
    request = AdvisorProjectGenerationRequest(
        interests=["AI", "Healthcare"],
        level="intermediate",
        duration_months=5,
        preferred_stack=["Flutter", "FastAPI", "Python"],
        project_type="mobile app",
        max_results=1,
    )
    sources = SourceSearchResponse(
        papers=[_build_source_paper()],
        repositories=[_build_source_repository()],
    )

    projects = advisor_service.generate_projects_rule_based(request, sources)

    assert projects
    assert projects[0].tech_stack[:3] == ["Flutter", "FastAPI", "Python"]


def test_generated_title_is_clean_and_short():
    request = AdvisorProjectGenerationRequest(
        interests=["AI", "Healthcare"],
        level="intermediate",
        duration_months=5,
        preferred_stack=["Flutter", "FastAPI", "Python"],
        project_type="mobile app",
        max_results=1,
    )
    paper = _build_source_paper()
    repository = _build_source_repository()

    title = advisor_service._build_rule_based_title(request, paper, repository, 0)

    assert len(title.split()) <= 8
    assert paper.title not in title
    assert "Inspired by" not in title
    assert "Product Based on" not in title


def test_rule_based_generation_produces_distinct_titles():
    request = AdvisorProjectGenerationRequest(
        interests=["AI", "Healthcare"],
        level="intermediate",
        duration_months=5,
        preferred_stack=["Flutter", "FastAPI", "Python"],
        project_type="mobile app",
        max_results=3,
    )
    sources = SourceSearchResponse(
        papers=[
            _build_source_paper(),
            _build_referral_source_paper(),
            _build_lifecycle_source_paper(),
        ],
        repositories=[
            _build_source_repository(),
            _build_lifecycle_repository(),
        ],
    )

    projects = advisor_service.generate_projects_rule_based(request, sources)
    titles = [project.title for project in projects]

    assert len(projects) == 3
    assert len(set(titles)) == len(titles)


def test_agriculture_generation_has_no_healthcare_leakage_and_uses_domain_terms():
    request = AdvisorProjectGenerationRequest(
        interests=["agriculture"],
        level="intermediate",
        duration_months=1,
        preferred_stack=["Python", "FastAPI"],
        project_type="product",
        max_results=1,
    )
    sources = SourceSearchResponse(
        papers=[_build_agriculture_source_paper()],
        repositories=[],
    )

    projects = advisor_service.generate_projects_rule_based(request, sources)

    assert projects
    project = projects[0]
    forbidden_terms = ["patient", "doctor", "clinical", "healthcare", "referral", "medical"]
    combined_text = " ".join(
        [
            project.title,
            project.description,
            project.problem,
            project.solution,
            project.scope,
            *project.features,
        ]
    ).lower()

    assert all(term not in combined_text for term in forbidden_terms)
    assert any(
        keyword in project.title.lower()
        for keyword in ["crop", "field", "farm", "agriculture", "irrigation", "yield", "mission"]
    )
    assert any(
        keyword in " ".join(project.features).lower()
        for keyword in ["crop", "field", "farm", "irrigation", "yield", "pest", "mission"]
    )


def test_generic_titles_are_replaced_with_domain_specific_titles():
    request = AdvisorProjectGenerationRequest(
        interests=["agriculture"],
        level="intermediate",
        duration_months=1,
        preferred_stack=["Python", "FastAPI"],
        project_type="product",
        max_results=1,
    )
    bad_titles = [
        "Project Assistant",
        "Product Project Assistant",
        "Product Workflow Dashboard",
        "Product Patient Risk Analyzer",
    ]

    cleaned_titles = [
        advisor_service._clean_generated_title(
            bad_title,
            request,
            _build_agriculture_source_paper(),
            None,
            "Agriculture",
        )
        for bad_title in bad_titles
    ]

    assert all(cleaned_title not in bad_titles for cleaned_title in cleaned_titles)
    assert all("project assistant" not in cleaned_title.lower() for cleaned_title in cleaned_titles)


def test_weak_unrelated_healthcare_paper_scores_below_threshold():
    request = AdvisorProjectGenerationRequest(
        interests=["AI", "Healthcare"],
        level="intermediate",
        duration_months=5,
        preferred_stack=["Flutter", "FastAPI", "Python"],
        project_type="mobile app",
        max_results=3,
    )

    score = advisor_service._score_paper(_build_weak_healthcare_paper(), request)

    assert score < advisor_service._paper_score_threshold(request)


def test_github_filtering_rejects_meaningless_repository_names():
    payload = {
        "items": [
            {
                "name": "-L-",
                "full_name": "user/-L-",
                "description": "Healthcare app",
                "stargazers_count": 100,
                "language": "Python",
                "html_url": "https://github.com/user/-L-",
                "fork": False,
                "archived": False,
            },
            {
                "name": "test",
                "full_name": "user/test",
                "description": "Healthcare app",
                "stargazers_count": 100,
                "language": "Python",
                "html_url": "https://github.com/user/test",
                "fork": False,
                "archived": False,
            },
            {
                "name": "demo",
                "full_name": "user/demo",
                "description": "Healthcare app",
                "stargazers_count": 100,
                "language": "Python",
                "html_url": "https://github.com/user/demo",
                "fork": False,
                "archived": False,
            },
            {
                "name": ".",
                "full_name": "user/.",
                "description": "Healthcare app",
                "stargazers_count": 100,
                "language": "Python",
                "html_url": "https://github.com/user/dot",
                "fork": False,
                "archived": False,
            },
        ]
    }

    repositories = github_service._parse_repositories(
        payload, "flutter fastapi ai healthcare mobile app"
    )

    assert repositories == []


def test_single_repository_is_not_reused_blindly_across_all_projects():
    request = AdvisorProjectGenerationRequest(
        interests=["AI", "Healthcare"],
        level="intermediate",
        duration_months=5,
        preferred_stack=["Flutter", "FastAPI", "Python"],
        project_type="mobile app",
        max_results=3,
    )
    sources = SourceSearchResponse(
        papers=[
            _build_source_paper(),
            _build_referral_source_paper(),
            _build_lifecycle_source_paper(),
        ],
        repositories=[_build_source_repository()],
    )

    projects = advisor_service.generate_projects_rule_based(request, sources)
    github_links = [project.github_link for project in projects if project.github_link]

    assert github_links.count("https://github.com/openhealth/referral-assistant") <= 2
    assert sum(project.source_status == "real_sources" for project in projects) < len(projects)


def test_single_repository_creates_paper_only_results_when_needed():
    request = AdvisorProjectGenerationRequest(
        interests=["AI", "Healthcare"],
        level="intermediate",
        duration_months=5,
        preferred_stack=["Flutter", "FastAPI", "Python"],
        project_type="mobile app",
        max_results=3,
    )
    sources = SourceSearchResponse(
        papers=[
            _build_source_paper(),
            _build_referral_source_paper(),
            _build_lifecycle_source_paper(),
        ],
        repositories=[_build_source_repository()],
    )

    bundles = advisor_service._select_generation_bundles(request, sources)

    assert any(bundle.source_status == "paper_only" for bundle in bundles)
    assert not all(bundle.source_status == "real_sources" for bundle in bundles)


def test_generation_message_for_paper_only_projects_is_accurate():
    paper_only_project = _build_generated_project().model_copy(
        update={"source_status": "paper_only", "github_link": None}
    )

    message = advisor_service._build_generation_message(
        generated_projects=[paper_only_project],
        repositories_found=1,
    )

    assert "paper-backed" in message.lower()
    assert "relevance thresholds" in message.lower()
    assert "real sources" not in message.lower()
    assert "verified" not in message.lower()


def test_one_month_scope_is_compact_for_agriculture_projects():
    request = AdvisorProjectGenerationRequest(
        interests=["agriculture"],
        level="intermediate",
        duration_months=1,
        preferred_stack=["Python", "FastAPI"],
        project_type="product",
        max_results=1,
    )
    sources = SourceSearchResponse(
        papers=[_build_agriculture_source_paper()],
        repositories=[_build_agriculture_repository()],
    )

    projects = advisor_service.generate_projects_rule_based(request, sources)

    assert projects
    project = projects[0]
    assert len(project.weekly_milestones) <= 4
    assert "compact MVP" in project.scope
    assert len(project.features) <= 4
    assert any("limited time" in risk.lower() for risk in project.risks)


def test_chat_scope_guard_marks_out_of_scope():
    settings.enable_llm = False
    project = _build_generated_project()
    request = AdvisorChatRequest(
        project=project,
        messages=[ProjectChatMessage(role="user", content="What is the football score today?")],
    )

    response = advisor_service.chat_about_project(request)

    assert response.out_of_scope is True
    assert ENGLISH_SCOPE_REMINDER in response.reply


def test_chat_team_division_arabic_response():
    settings.enable_llm = False
    project = _build_generated_project()
    request = AdvisorChatRequest(
        project=project,
        messages=[
            ProjectChatMessage(
                role="user", content="احنا تلاتة في التيم، نقسم المشروع إزاي؟"
            )
        ],
    )

    response = advisor_service.chat_about_project(request)

    assert response.language == "ar"
    assert response.out_of_scope is False
    assert "تقسيم عملي لفريق من 3 أشخاص" in response.reply
    assert "العضو 1" in response.reply
    assert "العضو 2" in response.reply
    assert "العضو 3" in response.reply
