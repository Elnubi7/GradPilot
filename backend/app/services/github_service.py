import json
import logging
import re
from urllib import error, parse, request

from app.core.config import settings
from app.schemas.source_schema import SourceRepository


logger = logging.getLogger(__name__)


class GitHubService:
    def search_repositories(
        self,
        query: str,
        max_results: int = 5,
        query_candidates: list[str] | None = None,
    ) -> list[SourceRepository]:
        if not settings.enable_github or not query.strip():
            return []

        candidates = query_candidates or self._build_query_candidates(query)
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "GradPilot-Backend",
        }
        if settings.github_token:
            headers["Authorization"] = f"Bearer {settings.github_token}"

        logger.info("GitHub query candidates: %s", candidates)

        for index, candidate in enumerate(candidates, start=1):
            repositories = self._execute_search(
                candidate=candidate,
                candidate_index=index,
                max_results=max_results,
                headers=headers,
            )
            if repositories:
                logger.info(
                    "GitHub fallback query %s succeeded with %s repositories: %s",
                    index,
                    len(repositories),
                    candidate,
                )
                return repositories

        logger.info("GitHub search returned 0 repositories for all fallback queries.")
        return []

    def _execute_search(
        self,
        candidate: str,
        candidate_index: int,
        max_results: int,
        headers: dict[str, str],
    ) -> list[SourceRepository]:
        qualified_query = self._apply_search_qualifiers(candidate)
        encoded_query = parse.quote(qualified_query)
        url = (
            "https://api.github.com/search/repositories"
            f"?q={encoded_query}&sort=stars&order=desc&per_page={max_results}"
        )

        logger.info("Generated GitHub query %s: %s", candidate_index, qualified_query)
        logger.info("GitHub request URL %s: %s", candidate_index, url)

        try:
            http_request = request.Request(url=url, headers=headers, method="GET")
            with request.urlopen(
                http_request, timeout=settings.request_timeout_seconds
            ) as response:
                status_code = response.status
                payload = json.loads(response.read().decode("utf-8"))
            repositories = self._parse_repositories(payload, candidate)
            logger.info(
                "GitHub response status for query %s: %s", candidate_index, status_code
            )
            logger.info(
                "GitHub repositories count for query %s: %s",
                candidate_index,
                len(repositories),
            )
            return repositories
        except error.HTTPError as exc:
            logger.warning(
                "GitHub search failed for query %s with status %s: %s",
                candidate,
                exc.code,
                exc,
            )
            return []
        except (error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            logger.warning("GitHub search failed for query '%s': %s", candidate, exc)
            return []

    def _parse_repositories(
        self, payload: dict, candidate: str
    ) -> list[SourceRepository]:
        repositories_with_score: list[tuple[int, SourceRepository]] = []
        fallback_repositories: list[tuple[int, SourceRepository]] = []

        for item in payload.get("items", []):
            stars = item.get("stargazers_count", 0)
            html_url = item.get("html_url")
            if stars <= 10 or not isinstance(html_url, str) or not html_url.strip():
                continue

            if self._is_meaningless_repository(item):
                continue

            repository = SourceRepository(
                name=item.get("name", ""),
                full_name=item.get("full_name", ""),
                description=item.get("description") or "",
                stars=stars,
                language=item.get("language"),
                url=html_url,
            )
            practicality_score = self._score_repository(item, candidate)
            if practicality_score >= 50:
                repositories_with_score.append((practicality_score, repository))
            else:
                fallback_repositories.append((practicality_score, repository))

        repositories_with_score.sort(
            key=lambda item: (item[0], item[1].stars),
            reverse=True,
        )
        fallback_repositories.sort(
            key=lambda item: (item[0], item[1].stars),
            reverse=True,
        )

        if repositories_with_score:
            return [repository for _, repository in repositories_with_score]
        return [repository for _, repository in fallback_repositories]

    def _build_query_candidates(self, query: str) -> list[str]:
        normalized_tokens = self._normalize_keywords(query.split())
        token_text = " ".join(normalized_tokens)

        candidates = [
            f"{token_text} project app backend mobile",
            f"{token_text} app backend",
            token_text,
            "flutter fastapi python project",
        ]
        return self._deduplicate_candidates(candidates)

    def _apply_search_qualifiers(self, candidate: str) -> str:
        return f"{candidate} stars:>10 fork:false archived:false"

    def _score_repository(self, item: dict, candidate: str) -> int:
        score = 0
        name = (item.get("name") or "").lower()
        full_name = (item.get("full_name") or "").lower()
        description = (item.get("description") or "").lower()
        language = (item.get("language") or "").lower()
        repo_text = f"{name} {full_name} {description} {language}"
        candidate_keywords = self._normalize_keywords(candidate.split())

        if description:
            score += 18
        if item.get("language"):
            score += 10
        if item.get("fork") is False:
            score += 10
        if item.get("archived") is False:
            score += 10

        stars = item.get("stargazers_count", 0)
        if stars >= 1000:
            score += 20
        elif stars >= 250:
            score += 16
        elif stars >= 50:
            score += 12
        elif stars >= 10:
            score += 8

        practical_terms = [
            "app",
            "api",
            "assistant",
            "chatbot",
            "platform",
            "dashboard",
            "healthcare",
            "education",
            "flutter",
            "fastapi",
        ]
        score += min(20, sum(4 for term in practical_terms if term in repo_text))
        score += min(24, sum(6 for keyword in candidate_keywords if keyword in repo_text))

        if not description and stars < 50:
            score -= 25
        if any(keyword in repo_text for keyword in ["demo", "tutorial", "example", "experiment"]):
            score -= 8
        if len(name.strip()) <= 2:
            score -= 20
        return max(0, min(100, score))

    def _is_meaningless_repository(self, item: dict) -> bool:
        name = (item.get("name") or "").strip()
        full_name = (item.get("full_name") or "").strip()
        description = (item.get("description") or "").strip()
        stars = item.get("stargazers_count", 0)

        if not name or not full_name:
            return True
        if re.fullmatch(r"[\W_]+", name):
            return True
        if re.fullmatch(r"[\W_]+", full_name.replace("/", "")):
            return True
        if name.lower() in {"test", "demo", "sample", ".", "-l-", "tmp"}:
            return True
        if len(name.replace("-", "").replace("_", "").strip()) <= 2:
            return True
        if not description and stars < 50:
            return True
        return False

    def _normalize_keywords(self, keywords: list[str]) -> list[str]:
        normalized: list[str] = []
        for keyword in keywords:
            cleaned = keyword.strip().lower()
            if cleaned and cleaned not in normalized:
                normalized.append(cleaned)
        return normalized

    def _deduplicate_candidates(self, candidates: list[str]) -> list[str]:
        unique_candidates: list[str] = []
        seen: set[str] = set()

        for candidate in candidates:
            normalized_candidate = " ".join(candidate.split())
            if not normalized_candidate or normalized_candidate in seen:
                continue
            seen.add(normalized_candidate)
            unique_candidates.append(normalized_candidate)

        return unique_candidates


github_service = GitHubService()
