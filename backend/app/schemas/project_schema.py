from pydantic import BaseModel, Field, HttpUrl


class ProjectBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    category: str = Field(..., min_length=2, max_length=100)
    difficulty: str = Field(..., min_length=3, max_length=50)
    duration_months: int = Field(..., ge=1, le=24)
    tech_stack: list[str] = Field(..., min_length=1)
    description: str = Field(..., min_length=10)
    problem: str = Field(..., min_length=10)
    solution: str = Field(..., min_length=10)
    features: list[str] = Field(..., min_length=1)
    evaluation_metrics: list[str] = Field(..., min_length=1)
    paper_link: HttpUrl | None = None
    github_link: HttpUrl | None = None
    feasibility_score: int = Field(..., ge=0, le=100)
    scope: str | None = None
    architecture_summary: str | None = None
    weekly_milestones: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    source_status: str | None = None
    source_titles: list[str] = Field(default_factory=list)
    source_quality_score: int | None = Field(default=None, ge=0, le=100)
    paper_score: int | None = Field(default=None, ge=0, le=100)
    repository_score: int | None = Field(default=None, ge=0, le=100)


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=200)
    category: str | None = Field(default=None, min_length=2, max_length=100)
    difficulty: str | None = Field(default=None, min_length=3, max_length=50)
    duration_months: int | None = Field(default=None, ge=1, le=24)
    tech_stack: list[str] | None = Field(default=None, min_length=1)
    description: str | None = Field(default=None, min_length=10)
    problem: str | None = Field(default=None, min_length=10)
    solution: str | None = Field(default=None, min_length=10)
    features: list[str] | None = Field(default=None, min_length=1)
    evaluation_metrics: list[str] | None = Field(default=None, min_length=1)
    paper_link: HttpUrl | None = None
    github_link: HttpUrl | None = None
    feasibility_score: int | None = Field(default=None, ge=0, le=100)
    scope: str | None = None
    architecture_summary: str | None = None
    weekly_milestones: list[str] | None = Field(default=None, min_length=1)
    risks: list[str] | None = Field(default=None, min_length=1)
    source_status: str | None = None
    source_titles: list[str] | None = Field(default=None, min_length=1)
    source_quality_score: int | None = Field(default=None, ge=0, le=100)
    paper_score: int | None = Field(default=None, ge=0, le=100)
    repository_score: int | None = Field(default=None, ge=0, le=100)


class ProjectResponse(ProjectBase):
    id: int


class DeleteResponse(BaseModel):
    message: str
