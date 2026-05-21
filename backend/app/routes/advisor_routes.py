from fastapi import APIRouter

from app.controllers.advisor_controller import (
    build_blueprint,
    chat_about_project,
    export_markdown,
    generate_projects,
    recommend_projects,
)
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


router = APIRouter()


@router.post("/recommend", response_model=AdvisorRecommendationResponse)
def recommend_projects_route(
    request_data: AdvisorRecommendationRequest,
) -> AdvisorRecommendationResponse:
    return recommend_projects(request_data)


@router.post("/generate-projects", response_model=GeneratedProjectsResponse)
def generate_projects_route(
    request_data: AdvisorProjectGenerationRequest,
) -> GeneratedProjectsResponse:
    return generate_projects(request_data)


@router.post("/chat", response_model=AdvisorChatResponse)
def chat_route(request_data: AdvisorChatRequest) -> AdvisorChatResponse:
    return chat_about_project(request_data)


@router.post("/blueprint", response_model=ProjectBlueprint)
def blueprint_route(request_data: AdvisorBlueprintRequest) -> ProjectBlueprint:
    return build_blueprint(request_data)


@router.post("/export-markdown", response_model=MarkdownExportResponse)
def export_markdown_route(
    request_data: MarkdownExportRequest,
) -> MarkdownExportResponse:
    return export_markdown(request_data)
