from dataclasses import dataclass, field


@dataclass
class Project:
    id: int
    title: str
    category: str
    difficulty: str
    duration_months: int
    tech_stack: list[str]
    description: str
    problem: str
    solution: str
    features: list[str]
    evaluation_metrics: list[str]
    paper_link: str | None = None
    github_link: str | None = None
    feasibility_score: int = 0
    scope: str | None = None
    architecture_summary: str | None = None
    weekly_milestones: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    source_status: str | None = None
    source_titles: list[str] = field(default_factory=list)
    source_quality_score: int | None = None
    paper_score: int | None = None
    repository_score: int | None = None
