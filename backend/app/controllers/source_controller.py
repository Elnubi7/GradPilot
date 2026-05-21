from app.schemas.source_schema import SourceSearchResponse
from app.services.source_service import source_service


def search_sources(query: str) -> SourceSearchResponse:
    return source_service.search_sources(query)
