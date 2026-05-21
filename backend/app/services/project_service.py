from dataclasses import asdict

from fastapi import HTTPException, status
from sqlalchemy import Text, cast, or_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import SessionLocal
from app.db.models import SavedProject
from app.models.project_model import Project
from app.schemas.advisor_schema import GeneratedProject
from app.schemas.project_schema import (
    DeleteResponse,
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
)


class ProjectService:
    def __init__(self) -> None:
        self._projects: list[Project] = []

    def get_all_projects(self) -> list[ProjectResponse]:
        if self._use_database():
            with SessionLocal() as db:
                projects = db.scalars(
                    select(SavedProject).order_by(SavedProject.id)
                ).all()
                return [self._db_project_to_schema(project) for project in projects]
        return [self._to_schema(project) for project in self._projects]

    def get_project_by_id(self, project_id: int) -> ProjectResponse:
        if self._use_database():
            with SessionLocal() as db:
                project = self._find_db_project(db, project_id)
                return self._db_project_to_schema(project)

        project = self._find_project(project_id)
        return self._to_schema(project)

    def create_project(self, project_data: ProjectCreate) -> ProjectResponse:
        if self._use_database():
            payload = self._build_saved_project_payload(project_data.model_dump())
            with SessionLocal() as db:
                new_project = SavedProject(**payload)
                db.add(new_project)
                db.commit()
                db.refresh(new_project)
                self._sync_raw_project(db, new_project)
                db.commit()
                db.refresh(new_project)
                return self._db_project_to_schema(new_project)

        new_project = Project(
            id=self._generate_next_id(),
            **project_data.model_dump(),
        )
        self._projects.append(new_project)
        return self._to_schema(new_project)

    def update_project(
        self, project_id: int, project_data: ProjectUpdate
    ) -> ProjectResponse:
        if self._use_database():
            with SessionLocal() as db:
                project = self._find_db_project(db, project_id)
                self._apply_db_project_update(project, project_data)
                db.commit()
                db.refresh(project)
                self._sync_raw_project(db, project)
                db.commit()
                db.refresh(project)
                return self._db_project_to_schema(project)

        project_index = self._find_project_index(project_id)
        current_project = self._projects[project_index]
        updated_data = asdict(current_project)
        updated_data.update(project_data.model_dump(exclude_unset=True))
        updated_project = Project(**updated_data)
        self._projects[project_index] = updated_project
        return self._to_schema(updated_project)

    def delete_project(self, project_id: int) -> DeleteResponse:
        if self._use_database():
            with SessionLocal() as db:
                project = self._find_db_project(db, project_id)
                title = project.title
                db.delete(project)
                db.commit()
                return DeleteResponse(
                    message=f"Project '{title}' deleted successfully."
                )

        project_index = self._find_project_index(project_id)
        deleted_project = self._projects.pop(project_index)
        return DeleteResponse(
            message=f"Project '{deleted_project.title}' deleted successfully."
        )

    def search_projects(self, query: str) -> list[ProjectResponse]:
        normalized_query = query.strip().lower()
        if not normalized_query:
            return self.get_all_projects()

        if self._use_database():
            like_query = f"%{normalized_query}%"
            with SessionLocal() as db:
                projects = db.scalars(
                    select(SavedProject).where(
                        or_(
                            SavedProject.title.ilike(like_query),
                            SavedProject.category.ilike(like_query),
                            SavedProject.difficulty.ilike(like_query),
                            SavedProject.description.ilike(like_query),
                            cast(SavedProject.tech_stack, Text).ilike(like_query),
                        )
                    ).order_by(SavedProject.id)
                ).all()
                return [self._db_project_to_schema(project) for project in projects]

        matched_projects = [
            project
            for project in self._projects
            if self._matches_query(project, normalized_query)
        ]
        return [self._to_schema(project) for project in matched_projects]

    def get_project_entities(self) -> list[Project]:
        if self._use_database():
            return [self._schema_to_entity(project) for project in self.get_all_projects()]
        return list(self._projects)

    def save_generated_project(self, project_data: GeneratedProject) -> ProjectResponse:
        if self._use_database():
            with SessionLocal() as db:
                existing_project = self._find_existing_generated_project(db, project_data)
                if existing_project:
                    return self._db_project_to_schema(existing_project)

                payload = self._build_saved_project_payload(
                    project_data.model_dump(),
                    raw_project=project_data.model_dump(),
                )
                new_project = SavedProject(**payload)
                db.add(new_project)
                db.commit()
                db.refresh(new_project)
                return self._db_project_to_schema(new_project)

        existing_project = self._find_existing_in_memory_generated_project(project_data)
        if existing_project is not None:
            return self._to_schema(existing_project)

        generated_payload = project_data.model_dump()
        generated_payload["id"] = self._generate_next_id()
        new_project = Project(**generated_payload)
        self._projects.append(new_project)
        return self._to_schema(new_project)

    def _find_project(self, project_id: int) -> Project:
        for project in self._projects:
            if project.id == project_id:
                return project
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with id {project_id} not found.",
        )

    def _find_project_index(self, project_id: int) -> int:
        for index, project in enumerate(self._projects):
            if project.id == project_id:
                return index
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with id {project_id} not found.",
        )

    def _find_db_project(self, db: Session, project_id: int) -> SavedProject:
        project = db.get(SavedProject, project_id)
        if project is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with id {project_id} not found.",
            )
        return project

    def _generate_next_id(self) -> int:
        if not self._projects:
            return 1
        return max(project.id for project in self._projects) + 1

    def _matches_query(self, project: Project, query: str) -> bool:
        searchable_fields = [
            project.title,
            project.category,
            project.description,
            project.difficulty,
            " ".join(project.tech_stack),
        ]
        return any(query in field.lower() for field in searchable_fields)

    def _to_schema(self, project: Project) -> ProjectResponse:
        return ProjectResponse(**asdict(project))

    def _db_project_to_schema(self, project: SavedProject) -> ProjectResponse:
        return ProjectResponse(
            id=project.id,
            title=project.title,
            category=project.category,
            difficulty=project.difficulty,
            duration_months=project.duration_months,
            tech_stack=project.tech_stack or [],
            description=project.description,
            problem=project.problem,
            solution=project.solution,
            features=project.features or [],
            evaluation_metrics=project.evaluation_metrics or [],
            paper_link=project.paper_link,
            github_link=project.github_link,
            feasibility_score=project.feasibility_score,
            scope=project.scope,
            architecture_summary=project.architecture_summary,
            weekly_milestones=project.weekly_milestones or [],
            risks=project.risks or [],
            source_status=project.source_status,
            source_titles=project.source_titles or [],
            source_quality_score=project.source_quality_score,
            paper_score=project.paper_score,
            repository_score=project.repository_score,
        )

    def _schema_to_entity(self, project: ProjectResponse) -> Project:
        return Project(**project.model_dump())

    def _build_saved_project_payload(
        self,
        payload: dict,
        raw_project: dict | None = None,
    ) -> dict:
        return {
            "owner_user_id": payload.get("owner_user_id"),
            "title": payload["title"],
            "category": payload["category"],
            "difficulty": payload["difficulty"],
            "duration_months": payload["duration_months"],
            "tech_stack": payload.get("tech_stack", []),
            "description": payload["description"],
            "problem": payload["problem"],
            "solution": payload["solution"],
            "features": payload.get("features", []),
            "evaluation_metrics": payload.get("evaluation_metrics", []),
            "paper_link": self._normalize_link(payload.get("paper_link")),
            "github_link": self._normalize_link(payload.get("github_link")),
            "feasibility_score": payload.get("feasibility_score", 0),
            "scope": payload.get("scope"),
            "architecture_summary": payload.get("architecture_summary"),
            "weekly_milestones": payload.get("weekly_milestones", []),
            "risks": payload.get("risks", []),
            "source_status": payload.get("source_status"),
            "source_titles": payload.get("source_titles", []),
            "source_quality_score": payload.get("source_quality_score"),
            "paper_score": payload.get("paper_score"),
            "repository_score": payload.get("repository_score"),
            "raw_project": raw_project,
        }

    def _apply_db_project_update(
        self,
        project: SavedProject,
        project_data: ProjectUpdate,
    ) -> None:
        update_data = project_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if key in {"paper_link", "github_link"}:
                setattr(project, key, self._normalize_link(value))
            else:
                setattr(project, key, value)

    def _sync_raw_project(self, db: Session, project: SavedProject) -> None:
        project.raw_project = self._db_project_to_schema(project).model_dump(mode="json")
        db.add(project)

    def _find_existing_generated_project(
        self, db: Session, project_data: GeneratedProject
    ) -> SavedProject | None:
        statement = select(SavedProject).where(SavedProject.title == project_data.title)
        if project_data.paper_link:
            statement = statement.where(
                SavedProject.paper_link == str(project_data.paper_link)
            )
        else:
            statement = statement.where(SavedProject.paper_link.is_(None))

        if project_data.github_link:
            statement = statement.where(
                SavedProject.github_link == str(project_data.github_link)
            )
        else:
            statement = statement.where(SavedProject.github_link.is_(None))

        return db.scalars(statement).first()

    def _find_existing_in_memory_generated_project(
        self, project_data: GeneratedProject
    ) -> Project | None:
        paper_link = self._normalize_link(project_data.paper_link)
        github_link = self._normalize_link(project_data.github_link)
        for project in self._projects:
            if (
                project.title == project_data.title
                and project.paper_link == paper_link
                and project.github_link == github_link
            ):
                return project
        return None

    def _normalize_link(self, link: object) -> str | None:
        if link is None:
            return None
        normalized_link = str(link).strip()
        return normalized_link or None

    def _use_database(self) -> bool:
        return settings.enable_database


project_service = ProjectService()
