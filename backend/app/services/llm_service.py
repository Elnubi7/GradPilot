import json
import re
from urllib import error, request

from app.core.config import settings
from app.schemas.advisor_schema import (
    AdvisorProjectGenerationRequest,
    AdvisorRecommendationRequest,
    GeneratedProject,
    ProjectChatMessage,
    ProjectBlueprint,
    RecommendedProject,
)
from app.schemas.source_schema import SourcePaper, SourceRepository


class LLMService:
    def parse_generation_preferences(self, prompt_text: str) -> dict | None:
        if not settings.enable_llm or not prompt_text.strip():
            return None

        prompt = self._build_generation_preferences_prompt(prompt_text)
        response_text = self._generate_text(prompt)
        if not response_text:
            return None

        payload = self._parse_json_payload(response_text)
        if not payload:
            return None

        return payload

    def chat_about_project(
        self,
        project_context: dict,
        messages: list[ProjectChatMessage],
        system_prompt: str,
    ) -> str | None:
        if not settings.enable_llm:
            return None

        prompt = self._build_project_chat_prompt(
            project_context=project_context,
            messages=messages,
            system_prompt=system_prompt,
        )
        response_text = self._generate_text(prompt)
        if not response_text:
            return None

        cleaned_reply = self._clean_chat_reply(response_text)
        return cleaned_reply or None

    def rewrite_recommendation_explanations(
        self,
        recommendations: list[RecommendedProject],
        request_data: AdvisorRecommendationRequest,
    ) -> list[str] | None:
        if not settings.enable_llm or not recommendations:
            return None

        prompt = self._build_rewrite_prompt(recommendations, request_data)
        response_text = self._generate_text(prompt)
        if not response_text:
            return None

        return self._parse_explanations(response_text, len(recommendations))

    def generate_project_ideas(
        self,
        request_data: AdvisorProjectGenerationRequest,
        papers: list[SourcePaper],
        repositories: list[SourceRepository],
    ) -> list[dict] | None:
        if not settings.enable_llm or not (papers or repositories):
            return None

        prompt = self._build_project_generation_prompt(
            request_data=request_data,
            papers=papers,
            repositories=repositories,
        )
        response_text = self._generate_text(prompt)
        if not response_text:
            return None

        return self._parse_project_payload(
            response_text=response_text,
            expected_count=request_data.max_results,
        )

    def generate_project_blueprint(
        self,
        project: GeneratedProject,
    ) -> ProjectBlueprint | None:
        if not settings.enable_llm:
            return None

        prompt = self._build_blueprint_prompt(project)
        response_text = self._generate_text(prompt)
        if not response_text:
            return None

        payload = self._parse_json_payload(response_text)
        if not payload:
            return None

        try:
            blueprint = ProjectBlueprint(**payload)
        except Exception:
            return None

        blueprint.source_links = self._extract_source_links(project)
        return blueprint

    def _generate_text(self, prompt: str) -> str | None:
        provider = settings.llm_provider.strip().lower()

        if provider == "ollama":
            return self._generate_with_ollama(prompt)
        if provider == "openai":
            return self._generate_with_openai(prompt)
        if provider == "azure_openai":
            return self._generate_with_azure_openai(prompt)
        return None

    def _generate_with_ollama(self, prompt: str) -> str | None:
        url = f"{settings.ollama_base_url.rstrip('/')}/api/generate"
        payload = {
            "model": settings.ollama_model,
            "prompt": prompt,
            "stream": False,
        }

        try:
            body = json.dumps(payload).encode("utf-8")
            http_request = request.Request(
                url=url,
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with request.urlopen(
                http_request, timeout=settings.request_timeout_seconds
            ) as response:
                response_body = json.loads(response.read().decode("utf-8"))
            return response_body.get("response")
        except (error.URLError, error.HTTPError, TimeoutError, json.JSONDecodeError):
            return None

    def _generate_with_openai(self, prompt: str) -> str | None:
        if not settings.openai_api_key:
            return None
        return None

    def _generate_with_azure_openai(self, prompt: str) -> str | None:
        if not (
            settings.azure_openai_api_key
            and settings.azure_openai_endpoint
            and settings.azure_openai_deployment
        ):
            return None
        return None

    def _build_rewrite_prompt(
        self,
        recommendations: list[RecommendedProject],
        request_data: AdvisorRecommendationRequest,
    ) -> str:
        recommendation_payload = [
            {
                "title": item.project.title,
                "category": item.project.category,
                "difficulty": item.project.difficulty,
                "duration_months": item.project.duration_months,
                "tech_stack": item.project.tech_stack,
                "match_score": item.match_score,
                "original_explanation": item.explanation,
            }
            for item in recommendations
        ]

        return (
            "You are improving explanation text for a graduation project advisor.\n"
            "Rewrite each explanation to be concise, professional, and student-friendly.\n"
            "Do not change project selection, scores, titles, or technical facts.\n"
            "Do not invent or mention arXiv links, GitHub links, papers, or repositories.\n"
            'Return JSON only with this format: {"explanations":["...", "..."]}\n'
            f"Student request: {request_data.model_dump_json()}\n"
            f"Recommendations: {json.dumps(recommendation_payload)}"
        )

    def _build_project_chat_prompt(
        self,
        project_context: dict,
        messages: list[ProjectChatMessage],
        system_prompt: str,
    ) -> str:
        conversation_payload = [
            {"role": message.role, "content": message.content} for message in messages
        ]

        return (
            f"{system_prompt}\n"
            "Return plain text only.\n"
            f"Project context: {json.dumps(project_context, ensure_ascii=False)}\n"
            f"Conversation: {json.dumps(conversation_payload, ensure_ascii=False)}"
        )

    def _build_generation_preferences_prompt(self, prompt_text: str) -> str:
        return (
            "You extract project preference fields for a graduation project advisor.\n"
            "Do not generate project ideas.\n"
            "Only extract preferences from the user text.\n"
            "Support Arabic, English, and mixed Arabic-English input.\n"
            "Return JSON only with this exact structure:\n"
            '{'
            '"interests": [], '
            '"level": "", '
            '"duration_months": null, '
            '"preferred_stack": [], '
            '"project_type": "", '
            '"constraints": [], '
            '"team_size": null'
            '}\n'
            "Use null when duration_months or team_size is missing.\n"
            "Use concise canonical values for known stacks and interests.\n"
            f"User text: {prompt_text}"
        )

    def _build_project_generation_prompt(
        self,
        request_data: AdvisorProjectGenerationRequest,
        papers: list[SourcePaper],
        repositories: list[SourceRepository],
    ) -> str:
        papers_payload = [
            {
                "title": paper.title,
                "summary": paper.summary,
                "authors": paper.authors,
                "published": paper.published,
            }
            for paper in papers[: request_data.max_results]
        ]
        repositories_payload = [
            {
                "name": repository.name,
                "full_name": repository.full_name,
                "description": repository.description,
                "stars": repository.stars,
                "language": repository.language,
            }
            for repository in repositories[: request_data.max_results]
        ]

        return (
            "You are generating graduation project ideas for computer science students.\n"
            "Use only the provided real arXiv and GitHub source candidates.\n"
            "Do not invent links and do not output paper_link or github_link.\n"
            "Keep project titles clean, specific, and preferably under 8 words.\n"
            "Do not copy full paper titles into project titles.\n"
            "Do not repeat identical titles or near-identical project angles across the response.\n"
            "Use different source themes when available, such as assistant, dashboard, analyzer, triage tool, privacy monitor, referral manager, prediction system, or patient support app.\n"
            "If the source set only supports fewer distinct strong projects, return fewer projects instead of repeating the same idea.\n"
            "Preserve the requested tech stack whenever possible, especially Flutter, FastAPI, and Python when the student asked for them.\n"
            "Descriptions should explain what the app does, who it helps, why it is source-backed, and which stack is relevant.\n"
            "Avoid generic phrases such as 'Build a ai platform' or 'source-driven workflow'.\n"
            "Use correct grammar such as 'an AI-powered assistant'.\n"
            "Make features domain-specific and practical.\n"
            "Make evaluation metrics match the project type and domain.\n"
            "You may generate only these fields: title, category, difficulty, duration_months, "
            "tech_stack, description, problem, solution, features, evaluation_metrics, scope, "
            "weekly_milestones, risks, architecture_summary, feasibility_score.\n"
            "Use difficulty values only from easy, medium, hard.\n"
            "Weekly milestones should be concise strings.\n"
            'Return JSON only with this format: {"projects":[{...}]}\n'
            f"Student request: {request_data.model_dump_json()}\n"
            f"Paper candidates: {json.dumps(papers_payload)}\n"
            f"Repository candidates: {json.dumps(repositories_payload)}"
        )

    def _build_blueprint_prompt(self, project: GeneratedProject) -> str:
        project_payload = {
            "title": project.title,
            "category": project.category,
            "difficulty": project.difficulty,
            "duration_months": project.duration_months,
            "tech_stack": project.tech_stack,
            "description": project.description,
            "problem": project.problem,
            "solution": project.solution,
            "features": project.features,
            "evaluation_metrics": project.evaluation_metrics,
            "scope": project.scope,
            "architecture_summary": project.architecture_summary,
            "weekly_milestones": project.weekly_milestones,
            "risks": project.risks,
            "source_titles": project.source_titles,
            "source_status": project.source_status,
        }

        return (
            "You are expanding a graduation project idea into a practical implementation blueprint.\n"
            "Use only the provided project information.\n"
            "Do not invent paper or GitHub links, and do not include source_links in your output.\n"
            "Return JSON only with these fields: project_title, refined_problem_statement, objectives, "
            "target_users, core_features, optional_features, system_architecture, backend_modules, "
            "flutter_screens, database_or_storage_plan, api_endpoints, ai_pipeline, weekly_milestones, "
            "evaluation_metrics, risks, presentation_outline.\n"
            f"Project: {json.dumps(project_payload)}"
        )

    def _parse_explanations(
        self, response_text: str, expected_count: int
    ) -> list[str] | None:
        json_text = self._extract_json_object(response_text)
        if not json_text:
            return None

        try:
            payload = json.loads(json_text)
        except json.JSONDecodeError:
            return None

        explanations = payload.get("explanations")
        if not isinstance(explanations, list) or len(explanations) != expected_count:
            return None

        cleaned_explanations = [
            explanation.strip()
            for explanation in explanations
            if isinstance(explanation, str) and explanation.strip()
        ]
        if len(cleaned_explanations) != expected_count:
            return None
        return cleaned_explanations

    def _parse_project_payload(
        self, response_text: str, expected_count: int
    ) -> list[dict] | None:
        payload = self._parse_json_payload(response_text)
        if not payload:
            return None

        projects = payload.get("projects")
        if not isinstance(projects, list) or not projects:
            return None

        normalized_projects = [item for item in projects if isinstance(item, dict)]
        if not normalized_projects:
            return None

        return normalized_projects[:expected_count]

    def _parse_json_payload(self, response_text: str) -> dict | None:
        json_text = self._extract_json_object(response_text)
        if not json_text:
            return None

        try:
            payload = json.loads(json_text)
        except json.JSONDecodeError:
            return None

        if not isinstance(payload, dict):
            return None
        return payload

    def _extract_source_links(self, project: GeneratedProject) -> list[str]:
        links: list[str] = []
        if project.paper_link:
            links.append(project.paper_link)
        if project.github_link:
            links.append(project.github_link)
        return links

    def _clean_chat_reply(self, response_text: str) -> str:
        cleaned_text = re.sub(r"https?://\S+|www\.\S+", "", response_text)
        cleaned_text = " ".join(cleaned_text.split())
        return cleaned_text[:700].strip()

    def _extract_json_object(self, response_text: str) -> str | None:
        start_index = response_text.find("{")
        end_index = response_text.rfind("}")
        if start_index == -1 or end_index == -1 or end_index <= start_index:
            return None
        return response_text[start_index : end_index + 1]


llm_service = LLMService()
