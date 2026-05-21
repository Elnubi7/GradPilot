from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "GradPilot API"
    app_env: str = "development"
    app_version: str = "1.1.0"
    app_description: str = (
        "FastAPI backend for serving graduation project ideas and advisor recommendations."
    )
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/gradpilot"
    enable_database: bool = False

    cors_allow_origins: str = "*"

    arxiv_base_url: str = "https://export.arxiv.org/api/query"
    arxiv_max_results: int = Field(default=5, ge=1, le=20)
    arxiv_sort_by: str = "relevance"
    arxiv_sort_order: str = "descending"

    llm_provider: str = "ollama"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"

    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"

    azure_openai_api_key: str | None = None
    azure_openai_endpoint: str | None = None
    azure_openai_deployment: str | None = None

    github_token: str | None = None

    enable_llm: bool = True
    enable_arxiv: bool = True
    enable_github: bool = True

    request_timeout_seconds: int = Field(default=15, ge=1, le=120)

    @property
    def cors_allowed_origins(self) -> list[str]:
        raw_value = self.cors_allow_origins.strip()
        if not raw_value:
            return ["*"]
        if raw_value == "*":
            return ["*"]
        return [origin.strip() for origin in raw_value.split(",") if origin.strip()]


settings = Settings()
