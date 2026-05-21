from pydantic import BaseModel, HttpUrl, field_validator


class SourcePaper(BaseModel):
    title: str
    summary: str
    authors: list[str]
    published: str
    link: HttpUrl

    @field_validator("link")
    @classmethod
    def validate_arxiv_link(cls, value: HttpUrl) -> HttpUrl:
        link = str(value)
        if "arxiv.org" not in link or "/search" in link:
            raise ValueError("paper_link must be a real arXiv item URL.")
        return value


class SourceRepository(BaseModel):
    name: str
    full_name: str
    description: str
    stars: int
    language: str | None = None
    url: HttpUrl

    @field_validator("url")
    @classmethod
    def validate_github_url(cls, value: HttpUrl) -> HttpUrl:
        link = str(value)
        if "github.com" not in link or "/search" in link:
            raise ValueError("github_link must be a real GitHub repository URL.")
        return value


class SourceSearchResponse(BaseModel):
    papers: list[SourcePaper]
    repositories: list[SourceRepository]
