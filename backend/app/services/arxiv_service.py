import logging
from urllib import error, parse, request
from xml.etree import ElementTree

from app.core.config import settings
from app.schemas.source_schema import SourcePaper


logger = logging.getLogger(__name__)


class ArxivService:
    def search_papers(self, query: str, max_results: int | None = None) -> list[SourcePaper]:
        if not settings.enable_arxiv or not query.strip():
            return []

        result_limit = max_results or settings.arxiv_max_results
        encoded_query = parse.quote(query.strip())
        url = (
            f"{settings.arxiv_base_url}"
            f"?search_query=all:{encoded_query}"
            f"&start=0&max_results={result_limit}"
            f"&sortBy={settings.arxiv_sort_by}"
            f"&sortOrder={settings.arxiv_sort_order}"
        )

        try:
            with request.urlopen(url, timeout=settings.request_timeout_seconds) as response:
                xml_data = response.read()
            return self._parse_entries(xml_data)
        except error.HTTPError as exc:
            if exc.code == 429:
                logger.warning("arXiv rate limited. Try again later.")
                return []
            logger.warning("arXiv search failed for query '%s': %s", query, exc)
            return []
        except (error.URLError, error.HTTPError, TimeoutError, ElementTree.ParseError) as exc:
            logger.warning("arXiv search failed for query '%s': %s", query, exc)
            return []

    def _parse_entries(self, xml_data: bytes) -> list[SourcePaper]:
        root = ElementTree.fromstring(xml_data)
        namespace = {"atom": "http://www.w3.org/2005/Atom"}
        papers: list[SourcePaper] = []

        for entry in root.findall("atom:entry", namespace):
            title = self._get_text(entry, "atom:title", namespace)
            summary = self._get_text(entry, "atom:summary", namespace)
            published = self._get_text(entry, "atom:published", namespace)
            link = self._get_text(entry, "atom:id", namespace)
            authors = [
                author_name.text.strip()
                for author_name in entry.findall("atom:author/atom:name", namespace)
                if author_name.text
            ]

            if not title or not link:
                continue

            papers.append(
                SourcePaper(
                    title=" ".join(title.split()),
                    summary=" ".join(summary.split()),
                    authors=authors,
                    published=published,
                    link=link,
                )
            )

        return papers

    def _get_text(
        self, entry: ElementTree.Element, path: str, namespace: dict[str, str]
    ) -> str:
        node = entry.find(path, namespace)
        if node is None or node.text is None:
            return ""
        return node.text.strip()


arxiv_service = ArxivService()
