from fastapi import APIRouter, Query

from app.controllers.source_controller import search_sources
from app.schemas.source_schema import SourceSearchResponse


router = APIRouter()


@router.get("/search", response_model=SourceSearchResponse)
def search_sources_route(
    query: str = Query(..., min_length=1),
) -> SourceSearchResponse:
    return search_sources(query)
