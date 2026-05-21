from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from app.schemas.source_schema import SourcePaper, SourceRepository


class AdvisorBaseRequest(BaseModel):
    interests: list[str] = Field(..., min_length=1)
    level: str = Field(..., min_length=2, max_length=50)
    duration_months: int = Field(..., ge=1, le=24)
    preferred_stack: list[str] = Field(default_factory=list)


class AdvisorRecommendationRequest(AdvisorBaseRequest):
    include_sources: bool = True


class AdvisorProjectGenerationRequest(AdvisorBaseRequest):
    interests: list[str] = Field(default_factory=list)
    level: str | None = None
    duration_months: int | None = Field(default=None, ge=1, le=24)
    preferred_stack: list[str] = Field(default_factory=list)
    prompt_text: str | None = Field(default=None, max_length=4000)
    project_type: str = "product"
    max_results: int = Field(default=5, ge=1, le=10)

    @model_validator(mode="after")
    def validate_preferences(self) -> "AdvisorProjectGenerationRequest":
        has_structured_data = any(
            [
                bool(self.interests),
                bool((self.level or "").strip()),
                self.duration_months is not None,
                bool(self.preferred_stack),
            ]
        )
        if not has_structured_data and not (self.prompt_text or "").strip():
            raise ValueError(
                "Provide structured preferences or prompt_text for project generation."
            )
        return self


class ParsedPreferences(BaseModel):
    interests: list[str] = Field(default_factory=list)
    level: str = ""
    duration_months: int | None = None
    preferred_stack: list[str] = Field(default_factory=list)
    project_type: str = ""
    constraints: list[str] = Field(default_factory=list)
    team_size: int | None = None
    source: Literal["llm", "rule_based", "structured"] = "structured"


class GeneratedProject(BaseModel):
    id: int
    title: str
    category: str
    difficulty: str
    duration_months: int = Field(..., ge=1, le=24)
    tech_stack: list[str] = Field(..., min_length=1)
    description: str
    problem: str
    solution: str
    features: list[str] = Field(..., min_length=1)
    evaluation_metrics: list[str] = Field(..., min_length=1)
    paper_link: str | None = None
    github_link: str | None = None
    feasibility_score: int = Field(..., ge=0, le=100)
    scope: str
    architecture_summary: str
    weekly_milestones: list[str] = Field(..., min_length=1)
    risks: list[str] = Field(..., min_length=1)
    source_status: Literal["real_sources", "paper_only", "repo_only"]
    source_titles: list[str] = Field(default_factory=list)
    source_quality_score: int = Field(..., ge=0, le=100)
    paper_score: int = Field(..., ge=0, le=100)
    repository_score: int = Field(..., ge=0, le=100)


class RecommendedProject(BaseModel):
    project: GeneratedProject
    explanation: str
    match_score: int = Field(..., ge=0, le=100)


class GeneratedProjectsResponse(BaseModel):
    generated_projects: list[GeneratedProject]
    papers_found: int
    repositories_found: int
    message: str
    parsed_preferences: ParsedPreferences


class ProjectChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., min_length=1, max_length=2000)


class AdvisorChatRequest(BaseModel):
    project: GeneratedProject
    messages: list[ProjectChatMessage] = Field(..., min_length=1, max_length=20)
    user_id: int | None = None
    session_id: int | None = None


class AdvisorChatResponse(BaseModel):
    reply: str
    language: Literal["ar", "en", "mixed"]
    out_of_scope: bool
    session_id: int | None = None


class ChatMessageResponse(BaseModel):
    id: int
    session_id: int
    role: str
    content: str
    created_at: datetime


class ChatSessionResponse(BaseModel):
    id: int
    user_id: int | None = None
    project_id: int | None = None
    title: str
    project_snapshot: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class ChatSessionDetailResponse(ChatSessionResponse):
    messages: list[ChatMessageResponse] = Field(default_factory=list)


class AdvisorRecommendationResponse(BaseModel):
    recommended_projects: list[RecommendedProject]
    papers: list[SourcePaper] = Field(default_factory=list)
    repositories: list[SourceRepository] = Field(default_factory=list)
    message: str = "Generated from real sources."


class ProjectBlueprint(BaseModel):
    project_title: str
    refined_problem_statement: str
    objectives: list[str] = Field(..., min_length=1)
    target_users: list[str] = Field(..., min_length=1)
    core_features: list[str] = Field(..., min_length=1)
    optional_features: list[str] = Field(default_factory=list)
    system_architecture: str
    backend_modules: list[str] = Field(..., min_length=1)
    flutter_screens: list[str] = Field(..., min_length=1)
    database_or_storage_plan: str
    api_endpoints: list[str] = Field(..., min_length=1)
    ai_pipeline: str
    weekly_milestones: list[str] = Field(..., min_length=1)
    evaluation_metrics: list[str] = Field(..., min_length=1)
    risks: list[str] = Field(..., min_length=1)
    presentation_outline: list[str] = Field(..., min_length=1)
    source_links: list[str] = Field(default_factory=list)


class AdvisorBlueprintRequest(BaseModel):
    project_id: int | None = None
    project: GeneratedProject | None = None

    @model_validator(mode="after")
    def validate_source(self) -> "AdvisorBlueprintRequest":
        if self.project_id is None and self.project is None:
            raise ValueError("Provide either project_id or project.")
        return self


class MarkdownExportRequest(BaseModel):
    project: GeneratedProject | None = None
    blueprint: ProjectBlueprint | None = None

    @model_validator(mode="after")
    def validate_payload(self) -> "MarkdownExportRequest":
        if self.project is None and self.blueprint is None:
            raise ValueError("Provide either project or blueprint.")
        return self


class MarkdownExportResponse(BaseModel):
    markdown: str
