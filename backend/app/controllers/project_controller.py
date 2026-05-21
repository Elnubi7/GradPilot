from app.schemas.advisor_schema import GeneratedProject
from app.schemas.project_schema import (
    DeleteResponse,
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
)
from app.services.project_service import project_service


def get_all_projects() -> list[ProjectResponse]:
    return project_service.get_all_projects()


def get_project_by_id(project_id: int) -> ProjectResponse:
    return project_service.get_project_by_id(project_id)


def create_project(project_data: ProjectCreate) -> ProjectResponse:
    return project_service.create_project(project_data)


def update_project(project_id: int, project_data: ProjectUpdate) -> ProjectResponse:
    return project_service.update_project(project_id, project_data)


def delete_project(project_id: int) -> DeleteResponse:
    return project_service.delete_project(project_id)


def search_projects(query: str) -> list[ProjectResponse]:
    return project_service.search_projects(query)


def save_generated_project(project_data: GeneratedProject) -> ProjectResponse:
    return project_service.save_generated_project(project_data)
