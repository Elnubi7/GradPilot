from fastapi import APIRouter, Query, status

from app.controllers.project_controller import (
    create_project,
    delete_project,
    get_all_projects,
    get_project_by_id,
    save_generated_project,
    search_projects,
    update_project,
)
from app.schemas.advisor_schema import GeneratedProject
from app.schemas.project_schema import (
    DeleteResponse,
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
)


router = APIRouter()


@router.get("", response_model=list[ProjectResponse])
def list_projects() -> list[ProjectResponse]:
    return get_all_projects()


@router.get("/search", response_model=list[ProjectResponse])
def search_projects_route(q: str = Query(..., min_length=1)) -> list[ProjectResponse]:
    return search_projects(q)


@router.post("/save-generated", response_model=ProjectResponse)
def save_generated_project_route(project_data: GeneratedProject) -> ProjectResponse:
    return save_generated_project(project_data)


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: int) -> ProjectResponse:
    return get_project_by_id(project_id)


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project_route(project_data: ProjectCreate) -> ProjectResponse:
    return create_project(project_data)


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project_route(
    project_id: int, project_data: ProjectUpdate
) -> ProjectResponse:
    return update_project(project_id, project_data)


@router.delete("/{project_id}", response_model=DeleteResponse)
def delete_project_route(project_id: int) -> DeleteResponse:
    return delete_project(project_id)
