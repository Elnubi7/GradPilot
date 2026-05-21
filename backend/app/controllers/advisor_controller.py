from app.schemas.advisor_schema import (
    AdvisorChatRequest,
    AdvisorChatResponse,
    AdvisorBlueprintRequest,
    AdvisorProjectGenerationRequest,
    AdvisorRecommendationRequest,
    AdvisorRecommendationResponse,
    GeneratedProjectsResponse,
    MarkdownExportRequest,
    MarkdownExportResponse,
    ProjectBlueprint,
)
from app.services.advisor_service import advisor_service


def recommend_projects(
    request_data: AdvisorRecommendationRequest,
) -> AdvisorRecommendationResponse:
    return advisor_service.recommend_projects(request_data)


def generate_projects(
    request_data: AdvisorProjectGenerationRequest,
) -> GeneratedProjectsResponse:
    return advisor_service.generate_projects_from_sources(request_data)


def build_blueprint(request_data: AdvisorBlueprintRequest) -> ProjectBlueprint:
    return advisor_service.generate_blueprint(request_data)


def chat_about_project(request_data: AdvisorChatRequest) -> AdvisorChatResponse:
    return advisor_service.chat_about_project(request_data)


def export_markdown(request_data: MarkdownExportRequest) -> MarkdownExportResponse:
    return advisor_service.export_markdown(request_data)
