import logging

from app.schemas.source_schema import SourcePaper, SourceRepository, SourceSearchResponse
from app.services.arxiv_service import arxiv_service
from app.services.github_service import github_service


logger = logging.getLogger(__name__)


class SourceService:
    def search_sources(
        self,
        arxiv_query_candidates: list[str] | None = None,
        max_results: int = 5,
        github_query_candidates: list[str] | None = None,
    ) -> SourceSearchResponse:
        papers = []
        repositories = []
        arxiv_candidates = arxiv_query_candidates or []
        github_candidates = github_query_candidates or []

        logger.info("arXiv query candidates: %s", arxiv_candidates)
        logger.info("GitHub query candidates: %s", github_candidates)

        papers = self._search_arxiv_with_fallback(
            query_candidates=arxiv_candidates,
            max_results=max_results,
        )
        repositories = self._search_github_with_fallback(
            query_candidates=github_candidates,
            max_results=max_results,
        )

        logger.info("Source search finished with %s papers and %s repositories.", len(papers), len(repositories))

        return SourceSearchResponse(
            papers=papers,
            repositories=repositories,
        )

    def _search_arxiv_with_fallback(
        self,
        query_candidates: list[str],
        max_results: int,
    ) -> list[SourcePaper]:
        for index, candidate in enumerate(query_candidates, start=1):
            try:
                papers = arxiv_service.search_papers(
                    query=candidate,
                    max_results=max_results,
                )
            except Exception as exc:
                logger.warning("arXiv source lookup failed for '%s': %s", candidate, exc)
                continue

            logger.info(
                "arXiv query %s returned %s papers: %s",
                index,
                len(papers),
                candidate,
            )
            if papers:
                logger.info("arXiv selected query %s: %s", index, candidate)
                return papers

        logger.info("arXiv search returned 0 papers for all fallback queries.")
        return []

    def _search_github_with_fallback(
        self,
        query_candidates: list[str],
        max_results: int,
    ) -> list[SourceRepository]:
        github_query_candidates = [
            candidate for candidate in query_candidates if candidate.strip()
        ]
        if not github_query_candidates:
            return []

        try:
            repositories = github_service.search_repositories(
                query=github_query_candidates[0],
                max_results=max_results,
                query_candidates=github_query_candidates,
            )
        except Exception as exc:
            logger.warning("GitHub source lookup failed: %s", exc)
            return []

        logger.info("GitHub final repository count: %s", len(repositories))
        return repositories


source_service = SourceService()
