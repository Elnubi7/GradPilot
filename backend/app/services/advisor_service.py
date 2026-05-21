import logging
import re
from dataclasses import dataclass
from datetime import datetime

from pydantic import ValidationError

from app.schemas.advisor_schema import (
    AdvisorChatRequest,
    AdvisorChatResponse,
    AdvisorBlueprintRequest,
    AdvisorProjectGenerationRequest,
    AdvisorRecommendationRequest,
    AdvisorRecommendationResponse,
    GeneratedProject,
    GeneratedProjectsResponse,
    MarkdownExportRequest,
    MarkdownExportResponse,
    ParsedPreferences,
    ProjectChatMessage,
    ProjectBlueprint,
    RecommendedProject,
)
from app.schemas.source_schema import SourcePaper, SourceRepository, SourceSearchResponse
from app.services.chat_service import chat_service
from app.services.domain_profiles import DOMAIN_PROFILES, GENERIC_DOMAIN_LABEL, DomainProfile
from app.services.llm_service import llm_service
from app.services.project_service import project_service
from app.services.source_service import source_service


logger = logging.getLogger(__name__)
NO_SOURCES_MESSAGE = (
    "No real arXiv or GitHub sources found for this query. Try broader keywords."
)
ARABIC_SCOPE_REMINDER = (
    "ملحوظة: ده خارج نطاق المشروع تقريبًا، من فضلك اسألني عن فكرة المشروع أو تنفيذه أو تقسيم المهام أو الـ architecture."
)
ENGLISH_SCOPE_REMINDER = (
    "Note: this is probably outside the project scope. Please ask me about the project idea, implementation, task division, or architecture."
)
MIXED_SCOPE_REMINDER = (
    "ملحوظة/Note: ده غالبًا خارج نطاق المشروع. اسألني عن فكرة المشروع أو التنفيذ أو task division أو architecture."
)
INTEREST_KEYWORDS = {
    "AI": ["ai", "artificial intelligence", "machine learning", "ml", "ذكاء اصطناعي", "تعلم آلي"],
    "Healthcare": ["healthcare", "health", "medical", "صحة", "طبي"],
    "Education": ["education", "learning", "تعليم", "تعلم", "student", "students"],
    "Cybersecurity": ["cybersecurity", "security", "أمن سيبراني", "سيكيورتي", "cyber"],
    "E-commerce": ["ecommerce", "e-commerce", "shopping", "تجارة", "بيع"],
    "Finance": ["finance", "fintech", "مال", "مالي"],
    "Construction": ["construction", "هندسة", "مقاولات"],
    "Legal": ["legal", "law", "قانون"],
}
STACK_KEYWORDS = {
    "Flutter": ["flutter", "فلاتر"],
    "FastAPI": ["fastapi", "fast api"],
    "Python": ["python", "بايثون"],
    "React": ["react"],
    "Node.js": ["node.js", "nodejs", "node js"],
    "PostgreSQL": ["postgresql", "postgres", "postgre"],
    "MongoDB": ["mongodb", "mongo db", "mongo"],
    "Firebase": ["firebase"],
    "Ollama": ["ollama"],
    "LLM": ["llm", "large language model"],
}
LEVEL_KEYWORDS = {
    "beginner": ["beginner", "easy", "سهل", "مبتدئ"],
    "intermediate": ["intermediate", "medium", "متوسط"],
    "advanced": ["advanced", "hard", "صعب", "متقدم"],
}


@dataclass
class GenerationSourceBundle:
    paper: SourcePaper | None
    repository: SourceRepository | None
    source_status: str
    paper_score: int
    repository_score: int
    source_quality_score: int
    theme: str


class AdvisorService:
    def recommend_projects(
        self, request_data: AdvisorRecommendationRequest
    ) -> AdvisorRecommendationResponse:
        generation_request = AdvisorProjectGenerationRequest(
            interests=request_data.interests,
            level=request_data.level,
            duration_months=request_data.duration_months,
            preferred_stack=request_data.preferred_stack,
            project_type="product",
            max_results=5,
        )
        generated_response = self.generate_projects_from_sources(generation_request)

        if not generated_response.generated_projects:
            return AdvisorRecommendationResponse(
                recommended_projects=[],
                papers=[],
                repositories=[],
                message=generated_response.message,
            )

        ranked_projects: list[RecommendedProject] = []
        for project in generated_response.generated_projects:
            match_score, explanation = self._score_project(project, request_data)
            ranked_projects.append(
                RecommendedProject(
                    project=project,
                    explanation=explanation,
                    match_score=match_score,
                )
            )

        ranked_projects.sort(key=lambda item: item.match_score, reverse=True)
        top_recommendations = ranked_projects[:5]
        self._apply_llm_explanations(top_recommendations, request_data)

        sources = (
            self._get_source_candidates(generation_request)
            if request_data.include_sources
            else SourceSearchResponse(papers=[], repositories=[])
        )

        return AdvisorRecommendationResponse(
            recommended_projects=top_recommendations,
            papers=sources.papers,
            repositories=sources.repositories,
            message="Recommended using real source-backed project ideas."
            if top_recommendations
            else NO_SOURCES_MESSAGE,
        )

    def generate_projects_from_sources(
        self, request_data: AdvisorProjectGenerationRequest
    ) -> GeneratedProjectsResponse:
        parsed_preferences = self._parse_prompt_preferences(request_data)
        merged_preferences = self._merge_preferences(request_data, parsed_preferences)
        effective_request = self._build_effective_generation_request(
            request_data=request_data,
            preferences=merged_preferences,
        )
        logger.info("Parsed generation preferences: %s", merged_preferences.model_dump())

        sources = self._get_source_candidates(effective_request)
        papers_found = len(sources.papers)
        repositories_found = len(sources.repositories)

        if not (papers_found or repositories_found):
            return GeneratedProjectsResponse(
                generated_projects=[],
                papers_found=0,
                repositories_found=0,
                message=NO_SOURCES_MESSAGE,
                parsed_preferences=merged_preferences,
            )

        generation_bundles = self._select_generation_bundles(effective_request, sources)
        if not generation_bundles:
            return GeneratedProjectsResponse(
                generated_projects=[],
                papers_found=papers_found,
                repositories_found=repositories_found,
                message="Generated 0 strong source-backed projects. Try broader keywords for more.",
                parsed_preferences=merged_preferences,
            )

        selected_sources = self._build_selected_sources_from_bundles(generation_bundles)
        generated_projects = self.generate_projects_with_llm(
            effective_request,
            generation_bundles,
            selected_sources,
        )
        if not generated_projects:
            generated_projects = self.generate_projects_rule_based(
                effective_request, generation_bundles
            )

        message = self._build_generation_message(
            generated_projects=generated_projects,
            repositories_found=repositories_found,
        )
        return GeneratedProjectsResponse(
            generated_projects=generated_projects[: effective_request.max_results],
            papers_found=papers_found,
            repositories_found=repositories_found,
            message=message,
            parsed_preferences=merged_preferences,
        )

    def _parse_prompt_preferences(
        self, request_data: AdvisorProjectGenerationRequest
    ) -> ParsedPreferences:
        prompt_text = (request_data.prompt_text or "").strip()
        if not prompt_text:
            return ParsedPreferences(
                interests=self._safe_string_list(request_data.interests),
                level=self._safe_string(request_data.level or ""),
                duration_months=request_data.duration_months,
                preferred_stack=self._normalize_stack_list(request_data.preferred_stack),
                project_type=self._canonicalize_project_type(request_data.project_type),
                constraints=[],
                team_size=None,
                source="structured",
            )

        llm_preferences = self._parse_prompt_with_llm(prompt_text)
        if llm_preferences is not None:
            return llm_preferences
        return self._parse_prompt_rule_based(prompt_text)

    def _parse_prompt_with_llm(self, prompt_text: str) -> ParsedPreferences | None:
        payload = llm_service.parse_generation_preferences(prompt_text)
        if not payload:
            return None

        duration_months = self._coerce_duration(payload.get("duration_months"))
        team_size = self._coerce_team_size(payload.get("team_size"))
        return ParsedPreferences(
            interests=self._normalize_interest_values(
                self._safe_string_list(payload.get("interests"))
            ),
            level=self._canonicalize_level(self._safe_string(payload.get("level", ""))),
            duration_months=duration_months,
            preferred_stack=self._normalize_stack_list(
                self._safe_string_list(payload.get("preferred_stack"))
            ),
            project_type=self._canonicalize_project_type(
                self._safe_string(payload.get("project_type", ""))
            ),
            constraints=self._safe_string_list(payload.get("constraints")),
            team_size=team_size,
            source="llm",
        )

    def _parse_prompt_rule_based(self, prompt_text: str) -> ParsedPreferences:
        normalized_text = self._normalize_text(prompt_text)
        interests = self._extract_keyword_matches(normalized_text, INTEREST_KEYWORDS)
        preferred_stack = self._extract_keyword_matches(normalized_text, STACK_KEYWORDS)
        level = self._extract_level_from_text(normalized_text)
        duration_months = self._extract_duration(prompt_text)
        team_size = self._extract_team_size(prompt_text)
        project_type = self._extract_project_type(normalized_text)
        constraints = self._extract_constraints(
            project_type=project_type,
            level=level,
            duration_months=duration_months,
            team_size=team_size,
        )

        return ParsedPreferences(
            interests=interests,
            level=level,
            duration_months=duration_months,
            preferred_stack=preferred_stack,
            project_type=project_type,
            constraints=constraints,
            team_size=team_size,
            source="rule_based",
        )

    def _merge_preferences(
        self,
        request_data: AdvisorProjectGenerationRequest,
        parsed_preferences: ParsedPreferences,
    ) -> ParsedPreferences:
        fields_set = request_data.model_fields_set
        prompt_text = request_data.prompt_text or ""
        has_prompt_text = bool(prompt_text.strip())
        detected_duration = self._extract_duration(prompt_text) if has_prompt_text else None
        detected_project_type = (
            self._extract_project_type(self._normalize_text(prompt_text))
            if has_prompt_text
            else ""
        )

        structured_interests = self._normalize_interest_values(
            self._sanitize_placeholder_list(request_data.interests)
        )
        interests = (
            structured_interests
            if "interests" in fields_set
            and (not has_prompt_text or not self._is_placeholder_value(structured_interests, "interests"))
            else parsed_preferences.interests
        )

        structured_level = self._canonicalize_level(request_data.level or "")
        level = (
            structured_level
            if "level" in fields_set
            and request_data.level is not None
            and (
                not has_prompt_text
                or not self._is_placeholder_value(structured_level, "level")
            )
            else parsed_preferences.level
        )

        structured_duration = self._coerce_duration(request_data.duration_months)
        duration_months = (
            structured_duration
            if "duration_months" in fields_set
            and request_data.duration_months is not None
            and (
                not has_prompt_text
                or not self._is_placeholder_value(
                    structured_duration,
                    "duration_months",
                    prompt_text=prompt_text,
                    detected_duration=detected_duration,
                )
            )
            else parsed_preferences.duration_months
        )

        structured_stack = self._normalize_stack_list(
            self._sanitize_placeholder_list(request_data.preferred_stack)
        )
        preferred_stack = (
            structured_stack
            if "preferred_stack" in fields_set
            and (
                not has_prompt_text
                or not self._is_placeholder_value(structured_stack, "preferred_stack")
            )
            else parsed_preferences.preferred_stack
        )

        structured_project_type = self._canonicalize_project_type(request_data.project_type)
        if "project_type" in fields_set and (
            not has_prompt_text
            or not self._is_placeholder_value(
                structured_project_type,
                "project_type",
                prompt_text=prompt_text,
                detected_project_type=detected_project_type,
            )
        ):
            project_type = structured_project_type
        else:
            project_type = parsed_preferences.project_type or structured_project_type

        merged = ParsedPreferences(
            interests=interests,
            level=level,
            duration_months=duration_months,
            preferred_stack=preferred_stack,
            project_type=project_type,
            constraints=parsed_preferences.constraints,
            team_size=parsed_preferences.team_size,
            source=parsed_preferences.source,
        )
        return self._apply_generation_defaults(merged, request_data.prompt_text or "")

    def _sanitize_placeholder_list(self, values: list[str] | None) -> list[str]:
        cleaned_values = self._safe_string_list(values or [])
        return [
            value
            for value in cleaned_values
            if value.strip().lower() not in {"string", "null", "none"}
        ]

    def _is_placeholder_value(
        self,
        value: object,
        field_name: str,
        prompt_text: str = "",
        detected_duration: int | None = None,
        detected_project_type: str = "",
    ) -> bool:
        if value is None:
            return True

        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"", "string", "null", "none"}:
                return True
            if field_name == "level" and normalized == "string":
                return True
            if (
                field_name == "project_type"
                and normalized == "product"
                and detected_project_type in {"mobile app", "web app", "research", "tool"}
            ):
                return True
            return False

        if isinstance(value, list):
            if not value:
                return True
            normalized_items = [
                item.strip().lower()
                for item in value
                if isinstance(item, str) and item.strip()
            ]
            return not normalized_items or all(
                item in {"string", "null", "none"} for item in normalized_items
            )

        if isinstance(value, int):
            if field_name == "duration_months" and detected_duration is not None and value <= 1:
                return True
            return False

        return False

    def _build_effective_generation_request(
        self,
        request_data: AdvisorProjectGenerationRequest,
        preferences: ParsedPreferences,
    ) -> AdvisorProjectGenerationRequest:
        return AdvisorProjectGenerationRequest(
            interests=preferences.interests,
            level=preferences.level,
            duration_months=preferences.duration_months,
            preferred_stack=preferences.preferred_stack,
            prompt_text=request_data.prompt_text,
            project_type=preferences.project_type or "product",
            max_results=request_data.max_results,
        )

    def generate_projects_with_llm(
        self,
        request_data: AdvisorProjectGenerationRequest,
        bundles: list[GenerationSourceBundle],
        sources: SourceSearchResponse,
    ) -> list[GeneratedProject]:
        project_payloads = llm_service.generate_project_ideas(
            request_data=request_data,
            papers=sources.papers,
            repositories=sources.repositories,
        )
        if not project_payloads:
            return []

        generated_projects: list[GeneratedProject] = []
        used_titles: set[str] = set()
        for index, (payload, bundle) in enumerate(
            zip(project_payloads, bundles, strict=False),
            start=1,
        ):
            project = self._build_project_from_payload(
                payload=payload,
                request_data=request_data,
                project_id=index,
                paper=bundle.paper,
                repository=bundle.repository,
                variant_index=index - 1,
                used_titles=used_titles,
            )
            if project is not None:
                generated_projects.append(project)

        return generated_projects

    def generate_projects_rule_based(
        self,
        request_data: AdvisorProjectGenerationRequest,
        sources: SourceSearchResponse | list[GenerationSourceBundle],
    ) -> list[GeneratedProject]:
        generation_bundles = (
            sources
            if isinstance(sources, list)
            else self._select_generation_bundles(request_data, sources)
        )
        generated_projects: list[GeneratedProject] = []
        used_titles: set[str] = set()

        for index, bundle in enumerate(generation_bundles[: request_data.max_results]):
            paper = bundle.paper
            repository = bundle.repository
            source_status = bundle.source_status
            category = self._determine_category(request_data, paper, repository)
            source_titles = self._build_source_titles(paper, repository)
            title = self._ensure_unique_title(
                self._build_rule_based_title(
                    request_data=request_data,
                    paper=paper,
                    repository=repository,
                    variant_index=index,
                ),
                request_data=request_data,
                paper=paper,
                repository=repository,
                variant_index=index,
                used_titles=used_titles,
            )

            generated_projects.append(
                GeneratedProject(
                    id=index + 1,
                    title=title,
                    category=category,
                    difficulty=self._difficulty_from_level(request_data.level),
                    duration_months=request_data.duration_months,
                    tech_stack=self._build_tech_stack(request_data, repository),
                    description=self._build_description(
                        request_data=request_data,
                        source_status=source_status,
                        source_titles=source_titles,
                        paper=paper,
                        repository=repository,
                    ),
                    problem=self._build_problem_statement(
                        request_data=request_data,
                        paper=paper,
                        repository=repository,
                    ),
                    solution=self._build_solution_statement(
                        request_data=request_data,
                        paper=paper,
                        repository=repository,
                    ),
                    features=self._build_features(
                        request_data=request_data,
                        paper=paper,
                        repository=repository,
                    ),
                    evaluation_metrics=self._build_evaluation_metrics(
                        category=category,
                        source_status=source_status,
                        paper=paper,
                        repository=repository,
                    ),
                    paper_link=str(paper.link) if paper else None,
                    github_link=str(repository.url) if repository else None,
                    feasibility_score=self._calculate_feasibility_score(
                        duration_months=request_data.duration_months,
                        preferred_stack=request_data.preferred_stack,
                        repository=repository,
                        source_status=source_status,
                    ),
                    scope=self._build_scope(request_data),
                    architecture_summary=self._build_architecture_summary(
                        request_data=request_data,
                        repository=repository,
                        source_status=source_status,
                    ),
                    weekly_milestones=self._build_weekly_milestones(request_data),
                    risks=self._build_risks(
                        source_status=source_status,
                        repository=repository,
                        category=category,
                        duration_months=request_data.duration_months,
                    ),
                    source_status=source_status,
                    source_titles=source_titles,
                    source_quality_score=bundle.source_quality_score,
                    paper_score=bundle.paper_score,
                    repository_score=bundle.repository_score,
                )
            )

        return generated_projects

    def generate_blueprint(
        self, request_data: AdvisorBlueprintRequest
    ) -> ProjectBlueprint:
        project = self._resolve_blueprint_project(request_data)
        llm_blueprint = llm_service.generate_project_blueprint(project)
        if llm_blueprint:
            return llm_blueprint
        return self._generate_rule_based_blueprint(project)

    def chat_about_project(self, request_data: AdvisorChatRequest) -> AdvisorChatResponse:
        latest_message = self._get_latest_user_message(request_data.messages)
        language = self._detect_language(latest_message)
        out_of_scope = self._is_out_of_scope(latest_message, request_data.project)
        project_context = self._build_project_context(request_data.project)
        system_prompt = self._build_chat_system_prompt(language, out_of_scope)

        reply = llm_service.chat_about_project(
            project_context=project_context,
            messages=request_data.messages,
            system_prompt=system_prompt,
        )
        if not reply:
            reply = self._rule_based_chat_reply(
                project=request_data.project,
                messages=request_data.messages,
                language=language,
                out_of_scope=out_of_scope,
            )
        reply = self._finalize_chat_reply(reply, language, out_of_scope)
        persisted_session_id = chat_service.persist_chat_exchange(
            project=request_data.project,
            messages=request_data.messages,
            reply=reply,
            user_id=request_data.user_id,
            session_id=request_data.session_id,
        )
        return AdvisorChatResponse(
            reply=reply,
            language=language,
            out_of_scope=out_of_scope,
            session_id=persisted_session_id,
        )

    def export_markdown(
        self, request_data: MarkdownExportRequest
    ) -> MarkdownExportResponse:
        if request_data.blueprint:
            markdown = self._build_blueprint_markdown(request_data.blueprint)
        else:
            markdown = self._build_project_markdown(request_data.project)
        return MarkdownExportResponse(markdown=markdown)

    def _resolve_blueprint_project(
        self, request_data: AdvisorBlueprintRequest
    ) -> GeneratedProject:
        if request_data.project is not None:
            return request_data.project

        saved_project = project_service.get_project_by_id(request_data.project_id)
        payload = saved_project.model_dump()
        payload["paper_link"] = str(payload["paper_link"]) if payload["paper_link"] else None
        payload["github_link"] = str(payload["github_link"]) if payload["github_link"] else None
        return GeneratedProject(**payload)

    def _generate_rule_based_blueprint(self, project: GeneratedProject) -> ProjectBlueprint:
        return ProjectBlueprint(
            project_title=project.title,
            refined_problem_statement=(
                f"{project.problem} The system should stay realistic for a {project.duration_months}-month graduation project "
                "and focus on delivering a measurable MVP."
            ),
            objectives=[
                "Build a working MVP based on the selected project idea.",
                "Validate the solution with measurable evaluation metrics.",
                "Document architecture, APIs, and implementation decisions clearly.",
            ],
            target_users=self._build_target_users(project),
            core_features=project.features[:4],
            optional_features=project.features[4:] or [
                "Notification and reminder support",
                "Exportable reports for supervisors",
            ],
            system_architecture=project.architecture_summary,
            backend_modules=self._build_backend_modules(project),
            flutter_screens=self._build_flutter_screens(project),
            database_or_storage_plan=self._build_storage_plan(project),
            api_endpoints=self._build_api_endpoints(project),
            ai_pipeline=self._build_ai_pipeline(project),
            weekly_milestones=project.weekly_milestones,
            evaluation_metrics=project.evaluation_metrics,
            risks=project.risks,
            presentation_outline=self._build_presentation_outline(project),
            source_links=self._build_source_links(project),
        )

    def _detect_language(self, message: str) -> str:
        has_arabic = bool(re.search(r"[\u0600-\u06FF]", message))
        has_english = bool(re.search(r"[A-Za-z]", message))
        if has_arabic and has_english:
            return "mixed"
        if has_arabic:
            return "ar"
        return "en"

    def _is_out_of_scope(self, message: str, project: GeneratedProject) -> bool:
        normalized = self._normalize_text(message)
        if not normalized:
            return False

        if self._extract_team_size(message) is not None:
            return False

        in_scope_keywords = [
            "project",
            "idea",
            "problem",
            "solution",
            "scope",
            "mvp",
            "architecture",
            "backend",
            "frontend",
            "flutter",
            "fastapi",
            "api",
            "database",
            "storage",
            "module",
            "screen",
            "timeline",
            "milestone",
            "week",
            "risk",
            "evaluation",
            "metric",
            "presentation",
            "defense",
            "doctor",
            "supervisor",
            "ollama",
            "ai",
            "task",
            "team",
            "split",
            "feature",
            "repo",
            "github",
            "paper",
            "arxiv",
            "implementation",
            "مشروع",
            "فكرة",
            "مشكلة",
            "حل",
            "نطاق",
            "معمارية",
            "اريكتكتشر",
            "architecture",
            "فلاتر",
            "flutter",
            "باك",
            "backend",
            "واجهة",
            "شاشة",
            "شاشات",
            "api",
            "endpoint",
            "قاعدة",
            "بيانات",
            "تخزين",
            "ذكاء",
            "مهام",
            "تقسيم",
            "تيم",
            "فريق",
            "جروب",
            "مراحل",
            "خطة",
            "جدول",
            "اسبوع",
            "أسبوع",
            "ريسك",
            "مخاطر",
            "تقييم",
            "مقاييس",
            "عرض",
            "presentation",
            "دكتور",
            "مشرف",
            "تنفيذ",
            "شرح",
        ]
        if any(keyword in normalized for keyword in in_scope_keywords):
            return False

        project_terms = {
            project.category.lower(),
            project.title.lower(),
            *[stack.lower() for stack in project.tech_stack],
            *[feature.lower() for feature in project.features[:5]],
        }
        if any(term and term in normalized for term in project_terms):
            return False

        return True

    def _extract_team_size(self, message: str) -> int | None:
        normalized = self._normalize_text(message)
        if not normalized:
            return None

        digit_patterns = [
            r"\bteam(?:\s+of)?\s+(\d{1,2})\b",
            r"\bgroup(?:\s+of)?\s+(\d{1,2})\b",
            r"\bwe are\s+(\d{1,2})\b",
            r"\b(\d{1,2})\s+(?:member|members|people)\b",
            r"\bاحنا\s+(\d{1,2})\b",
            r"\b(?:تيم|فريق|جروب)\s*(?:من|مكون من)?\s*(\d{1,2})\b",
            r"\b(\d{1,2})\s*(?:اعضاء|أعضاء)\b",
        ]
        for pattern in digit_patterns:
            match = re.search(pattern, normalized)
            if match:
                return self._coerce_team_size(int(match.group(1)))

        word_map = {
            "one": 1,
            "two": 2,
            "three": 3,
            "four": 4,
            "five": 5,
            "six": 6,
            "واحد": 1,
            "واحدة": 1,
            "اتنين": 2,
            "اثنين": 2,
            "اثنان": 2,
            "ثنين": 2,
            "تلاتة": 3,
            "ثلاثة": 3,
            "اربعة": 4,
            "أربعة": 4,
            "خمسة": 5,
            "سته": 6,
            "ستة": 6,
        }
        for word, value in word_map.items():
            explicit_patterns = [
                rf"\bteam(?:\s+of)?\s+{word}\b",
                rf"\bgroup(?:\s+of)?\s+{word}\b",
                rf"\bwe are\s+{word}\b",
                rf"\b{word}\s+(?:member|members|people)\b",
                rf"\bاحنا\s+{word}\b",
                rf"\b(?:تيم|فريق|جروب)\s+{word}\b",
            ]
            if any(re.search(pattern, normalized) for pattern in explicit_patterns):
                return value
        return None

    def _extract_duration(self, message: str) -> int | None:
        normalized = self._normalize_text(message)
        if not normalized:
            return None

        match = re.search(r"\b(\d{1,2})\s*(month|months|شهر|شهور|أشهر)\b", normalized)
        if not match:
            return None
        return self._coerce_duration(int(match.group(1)))

    def _extract_keyword_matches(
        self, text: str, keyword_map: dict[str, list[str]]
    ) -> list[str]:
        matches: list[str] = []
        for canonical, keywords in keyword_map.items():
            if any(keyword in text for keyword in keywords) and canonical not in matches:
                matches.append(canonical)
        return matches

    def _extract_level_from_text(self, text: str) -> str:
        for canonical, keywords in LEVEL_KEYWORDS.items():
            if any(keyword in text for keyword in keywords):
                return canonical
        return ""

    def _extract_project_type(self, text: str) -> str:
        if any(keyword in text for keyword in ["research-based", "research based", "research", "بحث"]):
            return "research"
        if any(
            keyword in text
            for keyword in ["mobile app", "mobile", "app", "application", "تطبيق", "موبايل", "mobile application"]
        ):
            return "mobile app"
        if any(keyword in text for keyword in ["web", "website", "ويب", "موقع"]):
            return "web app"
        if any(keyword in text for keyword in ["tool", "أداة"]):
            return "tool"
        if any(keyword in text for keyword in ["product", "منتج"]):
            return "product"
        return ""

    def _extract_constraints(
        self,
        project_type: str,
        level: str,
        duration_months: int | None,
        team_size: int | None,
    ) -> list[str]:
        constraints: list[str] = []
        if project_type:
            constraints.append(f"Build as a {project_type}")
        if level:
            constraints.append(f"Target difficulty: {level}")
        if duration_months is not None:
            constraints.append(f"Finish within {duration_months} months")
        if team_size is not None:
            constraints.append(f"Team size: {team_size}")
        return constraints

    def _build_project_context(self, project: GeneratedProject) -> dict:
        return {
            "title": project.title,
            "category": project.category,
            "difficulty": project.difficulty,
            "duration_months": project.duration_months,
            "tech_stack": project.tech_stack,
            "problem": project.problem,
            "solution": project.solution,
            "features": project.features,
            "scope": project.scope,
            "architecture_summary": project.architecture_summary,
            "weekly_milestones": project.weekly_milestones,
            "risks": project.risks,
            "evaluation_metrics": project.evaluation_metrics,
            "source_links": self._build_source_links(project),
        }

    def _build_chat_system_prompt(self, language: str, out_of_scope: bool) -> str:
        language_map = {
            "ar": "Arabic",
            "en": "English",
            "mixed": "a natural Arabic-English mixed style",
        }
        reminder = self._get_scope_reminder(language)

        prompt_parts = [
            "You are GradPilot Project Assistant.",
            "You help students understand and implement their selected graduation project.",
            f"Answer in {language_map.get(language, 'English')} and match the user's wording style.",
            "Keep answers practical and student-friendly.",
            "Use only the selected project data for project-specific facts.",
            "Do not invent GitHub or arXiv links.",
            "You can help with idea explanation, problem/solution, scope, Flutter screens, FastAPI modules, database/storage, AI pipeline, architecture, team task division, timeline, weekly milestones, risks, evaluation metrics, presentation questions, and how to explain the project to a doctor or supervisor.",
            "If the user mentions team size, split tasks clearly by member and adapt the split to the project's tech stack and features.",
        ]
        if out_of_scope:
            prompt_parts.append(
                f"If the question is outside scope, answer briefly and add this exact reminder at the end: {reminder}"
            )
        else:
            prompt_parts.append("Stay focused on the selected project and return plain text only.")
        return "\n".join(prompt_parts)

    def _rule_based_chat_reply(
        self,
        project: GeneratedProject,
        messages: list[ProjectChatMessage],
        language: str,
        out_of_scope: bool,
    ) -> str:
        question = self._get_latest_user_message(messages)
        normalized_question = self._normalize_text(question)
        if not question:
            return self._build_simple_project_reply(project, language)

        if out_of_scope:
            return self._build_out_of_scope_reply(language, question)

        team_size = self._extract_team_size(question)
        if team_size is not None:
            return self._build_team_division_reply(project, team_size, language)

        if any(
            keyword in normalized_question
            for keyword in ["scope", "mvp", "boundary", "نطاق", "حدود"]
        ):
            return self._build_scope_reply(project, language)
        if any(
            keyword in normalized_question
            for keyword in [
                "module",
                "modules",
                "api",
                "apis",
                "fastapi",
                "service",
                "endpoint",
                "backend",
                "باك",
                "موديول",
                "وحدة",
            ]
        ):
            return self._build_backend_reply(project, language)
        if any(
            keyword in normalized_question
            for keyword in [
                "architecture",
                "system",
                "design",
                "معمارية",
                "اريكتكتشر",
                "architecture",
            ]
        ):
            return self._build_architecture_reply(project, language)
        if any(
            keyword in normalized_question
            for keyword in ["flutter", "screen", "screens", "ui", "frontend", "واجهة", "شاشة", "شاشات"]
        ):
            return self._build_flutter_reply(project, language)
        if any(
            keyword in normalized_question
            for keyword in ["database", "storage", "db", "قاعدة", "بيانات", "تخزين"]
        ):
            return self._build_storage_reply(project, language)
        if any(
            keyword in normalized_question
            for keyword in ["ai", "model", "ollama", "pipeline", "ذكاء", "موديل"]
        ):
            return self._build_ai_reply(project, language)
        if any(
            keyword in normalized_question
            for keyword in ["timeline", "milestone", "week", "schedule", "خطة", "جدول", "اسبوع", "أسبوع"]
        ):
            return self._build_timeline_reply(project, language)
        if any(
            keyword in normalized_question
            for keyword in ["risk", "challenge", "issue", "ريسك", "مخاطر", "تحدي"]
        ):
            return self._build_risks_reply(project, language)
        if any(
            keyword in normalized_question
            for keyword in ["evaluation", "metric", "success", "قياس", "تقييم", "مقاييس"]
        ):
            return self._build_evaluation_reply(project, language)
        if any(
            keyword in normalized_question
            for keyword in [
                "presentation",
                "defense",
                "demo",
                "slide",
                "doctor",
                "supervisor",
                "عرض",
                "دكتور",
                "مشرف",
            ]
        ):
            return self._build_presentation_reply(project, language)
        if any(
            keyword in normalized_question
            for keyword in ["idea", "explain", "simple", "summary", "what is this", "فكرة", "شرح", "ملخص"]
        ):
            return self._build_simple_project_reply(project, language)

        return self._build_simple_project_reply(project, language)

    def _get_latest_user_message(self, messages: list[ProjectChatMessage]) -> str:
        for message in reversed(messages):
            if message.role == "user" and message.content.strip():
                return message.content.strip()
        return ""

    def _build_simple_project_reply(self, project: GeneratedProject, language: str) -> str:
        feature_text = ", ".join(project.features[:3])
        if language == "ar":
            return (
                f"{project.title} هو مشروع {project.category} مدته تقريبًا {project.duration_months} شهور. "
                f"المشكلة الأساسية: {project.problem} الحل المقترح: {project.solution} "
                f"وأهم المكونات: {feature_text}."
            )
        if language == "mixed":
            return (
                f"{project.title} is basically a {project.category} graduation project over {project.duration_months} months. "
                f"المشكلة الأساسية هي: {project.problem} والحل المقترح: {project.solution} "
                f"Core features: {feature_text}."
            )
        return (
            f"{project.title} is a {project.category.lower()} graduation project planned for {project.duration_months} months. "
            f"The core problem is {project.problem} The proposed solution is {project.solution} "
            f"Main features include {feature_text}."
        )

    def _build_scope_reply(self, project: GeneratedProject, language: str) -> str:
        if language == "ar":
            return (
                f"نطاق المشروع الحالي هو: {project.scope} "
                "ابدأوا بـ MVP واضح: workflow أساسي، API stable، وشاشتين أو ثلاث شاشات رئيسية، ثم أضيفوا تحسينات بعد كده."
            )
        if language == "mixed":
            return (
                f"The current scope is: {project.scope} "
                "ابدأوا بـ clear MVP: core workflow, stable API, and the main user screens first."
            )
        return (
            f"The current scope is: {project.scope} "
            "Start with a clear MVP around the core workflow, stable APIs, and the main user screens before adding extras."
        )

    def _build_backend_reply(self, project: GeneratedProject, language: str) -> str:
        modules = ", ".join(self._build_backend_modules(project))
        endpoints = ", ".join(self._build_api_endpoints(project)[:3])
        if language == "ar":
            return (
                f"اقترح تقسيم الـ FastAPI backend إلى modules زي: {modules}. "
                f"وأول endpoints عملية ممكن تكون: {endpoints}."
            )
        if language == "mixed":
            return (
                f"Suggested FastAPI modules: {modules}. "
                f"وأول useful endpoints: {endpoints}."
            )
        return (
            f"Suggested FastAPI modules: {modules}. "
            f"A practical first API set would be {endpoints}."
        )

    def _build_architecture_reply(self, project: GeneratedProject, language: str) -> str:
        backend_modules = ", ".join(self._build_backend_modules(project)[:3])
        if language == "ar":
            return (
                f"الـ architecture المناسب هو: {project.architecture_summary} "
                f"على مستوى التنفيذ: Flutter app للواجهة، FastAPI للخدمات والـ business logic، وموديولات أساسية مثل {backend_modules}."
            )
        if language == "mixed":
            return (
                f"Recommended architecture: {project.architecture_summary} "
                f"يعني Flutter for client experience, FastAPI for APIs and business logic, with modules like {backend_modules}."
            )
        return (
            f"Recommended architecture: {project.architecture_summary} "
            f"That means Flutter for the client side, FastAPI for APIs and business logic, with core modules such as {backend_modules}."
        )

    def _build_flutter_reply(self, project: GeneratedProject, language: str) -> str:
        screens = ", ".join(self._build_flutter_screens(project)[:5])
        if language == "ar":
            return f"الشاشات المقترحة في Flutter هي: {screens}. ابدأوا بالـ onboarding، dashboard، والـ main workflow الأول."
        if language == "mixed":
            return (
                f"Suggested Flutter screens: {screens}. "
                "ابدأوا بالـ onboarding, dashboard, and the main workflow screens first."
            )
        return (
            f"Suggested Flutter screens: {screens}. "
            "Start with onboarding, dashboard, and the main workflow screens first."
        )

    def _build_storage_reply(self, project: GeneratedProject, language: str) -> str:
        storage_plan = self._build_storage_plan(project)
        if language == "ar":
            return f"خطة التخزين المناسبة: {storage_plan}"
        if language == "mixed":
            return f"Database/storage plan: {storage_plan}"
        return f"Database and storage plan: {storage_plan}"

    def _build_ai_reply(self, project: GeneratedProject, language: str) -> str:
        ai_pipeline = self._build_ai_pipeline(project)
        if language == "ar":
            return f"الـ AI pipeline المقترح: {ai_pipeline}"
        if language == "mixed":
            return f"Suggested AI pipeline: {ai_pipeline}"
        return f"Suggested AI pipeline: {ai_pipeline}"

    def _build_timeline_reply(self, project: GeneratedProject, language: str) -> str:
        milestones = " | ".join(project.weekly_milestones[:4])
        if language == "ar":
            return f"ممكن تمشوا على timeline بسيط كده: {milestones}"
        if language == "mixed":
            return f"A simple timeline could be: {milestones}"
        return f"A simple timeline could be: {milestones}"

    def _build_risks_reply(self, project: GeneratedProject, language: str) -> str:
        risks = ", ".join(project.risks[:3])
        if language == "ar":
            return f"أهم المخاطر الحالية: {risks}. خففوا ده بتحديد scope واضح، واختبار الـ integrations بدري."
        if language == "mixed":
            return f"Main risks: {risks}. قللوا المخاطر بتثبيت الـ scope واختبار الـ integrations من بدري."
        return f"Main risks: {risks}. Reduce them with a fixed MVP scope and early integration testing."

    def _build_evaluation_reply(self, project: GeneratedProject, language: str) -> str:
        metrics = ", ".join(project.evaluation_metrics[:4])
        if language == "ar":
            return f"نجاح المشروع ممكن يتقاس بـ: {metrics}. اختاروا metric أو اتنين للـ demo ووضحوا طريقة القياس."
        if language == "mixed":
            return f"Useful evaluation metrics: {metrics}. اختاروا 1-2 key metrics and explain how you will measure them."
        return f"Useful evaluation metrics: {metrics}. Pick one or two key metrics for the demo and explain how you will measure them."

    def _build_presentation_reply(self, project: GeneratedProject, language: str) -> str:
        if language == "ar":
            return (
                "في الـ presentation ابدأ بالمشكلة، بعد كده الحل، ثم user flow، وبعدها architecture مختصر، "
                "وبعدين demo سريع، وفي النهاية evaluation metrics والمخاطر. "
                "ولو بتشرح لدكتور أو مشرف ركز على القيمة العملية، واقعية الـ scope، وليه التقنيات المختارة مناسبة."
            )
        if language == "mixed":
            return (
                "For the presentation, start with the problem, then the solution, then the user flow and a short architecture view, "
                "بعد كده اعمل demo سريع، واختم بالـ evaluation metrics والـ risks. "
                "With a doctor or supervisor, focus on practical value, realistic scope, and why the chosen stack fits."
            )
        return (
            "For the presentation, start with the problem, then the solution, then the user flow and a short architecture view, "
            "follow with a quick demo, and end with evaluation metrics and risks. "
            "When speaking to a doctor or supervisor, focus on practical value, realistic scope, and why the chosen stack fits."
        )

    def _build_out_of_scope_reply(self, language: str, question: str) -> str:
        normalized_question = self._normalize_text(question)

        if any(keyword in normalized_question for keyword in ["football", "match", "score", "كرة", "ماتش", "كورة"]):
            if language == "ar":
                return f"مش هقدر أوفر نتيجة ماتشات مباشرة أو live scores من هنا. {ARABIC_SCOPE_REMINDER}"
            if language == "mixed":
                return f"I cannot verify live football scores from this chat. {MIXED_SCOPE_REMINDER}"
            return f"I cannot verify live football scores from this project chat. {ENGLISH_SCOPE_REMINDER}"

        if any(keyword in normalized_question for keyword in ["politic", "election", "president", "سياسة", "انتخابات"]):
            if language == "ar":
                return f"أقدر أقول بشكل عام إن السياسة محتاجة مصادر محدثة جدًا، لكن مش ده نطاق الشات هنا. {ARABIC_SCOPE_REMINDER}"
            if language == "mixed":
                return f"Politics usually needs current verified sources, and this chat is not the right place for that. {MIXED_SCOPE_REMINDER}"
            return f"Politics usually needs current verified sources, and this chat is not the right place for that. {ENGLISH_SCOPE_REMINDER}"

        if any(keyword in normalized_question for keyword in ["cook", "recipe", "pasta", "طبخ", "اكلة", "أكلة"]):
            if language == "ar":
                return f"لو السؤال عن الطبخ بشكل عام: ابدأ بوصفة بسيطة ومقادير واضحة وخطوات قليلة. {ARABIC_SCOPE_REMINDER}"
            if language == "mixed":
                return f"For cooking, start with a simple recipe and clear steps. {MIXED_SCOPE_REMINDER}"
            return f"For cooking, start with a simple recipe and clear steps. {ENGLISH_SCOPE_REMINDER}"

        if any(keyword in normalized_question for keyword in ["travel", "trip", "visa", "hotel", "سفر", "فيزا", "فندق"]):
            if language == "ar":
                return f"في السفر عمومًا: حدد الميزانية، التواريخ، والمتطلبات الأساسية قبل الحجز. {ARABIC_SCOPE_REMINDER}"
            if language == "mixed":
                return f"For travel, fix your budget, dates, and core requirements first. {MIXED_SCOPE_REMINDER}"
            return f"For travel, fix your budget, dates, and core requirements first. {ENGLISH_SCOPE_REMINDER}"

        if language == "ar":
            return f"أقدر أديك إجابة عامة قصيرة، لكن الأفضل هنا نركز على مشروع التخرج. {ARABIC_SCOPE_REMINDER}"
        if language == "mixed":
            return f"I can give a short general answer, but it is better to stay focused on the project. {MIXED_SCOPE_REMINDER}"
        return f"I can give a short general answer, but it is better to stay focused on the project. {ENGLISH_SCOPE_REMINDER}"

    def _build_team_division_reply(
        self, project: GeneratedProject, team_size: int, language: str
    ) -> str:
        team_size = max(1, min(team_size, 6))
        roles = self._build_team_roles(project)
        assignments = self._distribute_team_roles(roles, team_size)

        if language == "ar":
            lines = [f"تقسيم عملي لفريق من {team_size} أشخاص:"]
            for index, assignment in enumerate(assignments, start=1):
                lines.append(f"- العضو {index}: {assignment}")
            lines.append("خلي كل عضو يسلّم جزء قابل للتجربة كل أسبوع عشان الدمج ما يتأخرش.")
            return "\n".join(lines)
        if language == "mixed":
            lines = [f"Practical split for a team of {team_size}:"]
            for index, assignment in enumerate(assignments, start=1):
                lines.append(f"- Member {index}: {assignment}")
            lines.append("اعملوا weekly integration so the mobile, backend, and AI parts stay aligned.")
            return "\n".join(lines)

        lines = [f"Practical split for a team of {team_size} members:"]
        for index, assignment in enumerate(assignments, start=1):
            lines.append(f"- Member {index}: {assignment}")
        lines.append("Keep a weekly integration checkpoint so the frontend, backend, and AI work stay aligned.")
        return "\n".join(lines)

    def _build_team_roles(self, project: GeneratedProject) -> list[str]:
        stack = [item.lower() for item in project.tech_stack]
        features_text = " ".join(project.features).lower()
        solution_text = f"{project.solution} {project.architecture_summary}".lower()
        uses_flutter = "flutter" in stack
        uses_fastapi = "fastapi" in stack or "python" in stack
        uses_ai = (
            project.category.lower() == "ai"
            or "ai" in solution_text
            or "assistant" in solution_text
            or "model" in solution_text
            or "prediction" in solution_text
            or "ai" in features_text
        )

        roles: list[str] = []
        if uses_flutter:
            roles.append(
                "Flutter UI, screens, navigation, state handling, and input validation"
            )
        else:
            roles.append("Frontend flow, user experience, and demo-ready screens")

        if uses_fastapi:
            roles.append(
                "FastAPI backend, endpoint design, business logic, integration, and database/storage"
            )
        else:
            roles.append("Backend services, APIs, and data persistence")

        if uses_ai:
            roles.append(
                "AI or Ollama integration, prompt or inference flow, evaluation metrics, testing, and presentation demo"
            )
        else:
            roles.append("Core project logic, quality assurance, testing, and presentation prep")

        roles.append("Testing, integration, bug fixing, documentation, and final presentation")
        roles.append("Deployment, analytics, polish tasks, and supervisor-facing documentation")
        return roles

    def _distribute_team_roles(self, roles: list[str], team_size: int) -> list[str]:
        if team_size == 1:
            return ["Own the full stack: " + "; ".join(roles[:4])]
        if team_size == 2:
            return [
                roles[0],
                f"{roles[1]}; {roles[2]}; {roles[3]}",
            ]
        if team_size == 3:
            return roles[:3]
        if team_size == 4:
            return roles[:4]
        if team_size == 5:
            return roles[:5]
        return [
            roles[0],
            roles[1],
            roles[2],
            "Testing, CI checks, integration, and bug fixing",
            "Documentation, diagrams, and presentation rehearsal",
            "Deployment, analytics, and final polish",
        ]

    def _finalize_chat_reply(
        self, reply: str, language: str, out_of_scope: bool
    ) -> str:
        lines = [re.sub(r"\s+", " ", line).strip() for line in reply.splitlines() if line.strip()]
        normalized_reply = "\n".join(lines)
        if not normalized_reply:
            normalized_reply = (
                self._build_out_of_scope_reply(language, "")
                if out_of_scope
                else ""
            )

        reminder = self._get_scope_reminder(language)
        if out_of_scope and reminder not in normalized_reply:
            separator = "\n" if "\n" in normalized_reply else " "
            normalized_reply = f"{normalized_reply}{separator}{reminder}".strip()
        return normalized_reply

    def _get_scope_reminder(self, language: str) -> str:
        if language == "ar":
            return ARABIC_SCOPE_REMINDER
        if language == "mixed":
            return MIXED_SCOPE_REMINDER
        return ENGLISH_SCOPE_REMINDER

    def _normalize_text(self, message: str) -> str:
        translation_table = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
        return message.lower().translate(translation_table).strip()

    def _score_project(
        self,
        project: GeneratedProject,
        request_data: AdvisorRecommendationRequest,
    ) -> tuple[int, str]:
        score = 0
        reasons: list[str] = []

        interests = [interest.strip().lower() for interest in request_data.interests]
        project_text = " ".join(
            [
                project.category,
                project.title,
                project.description,
                project.problem,
                project.solution,
                project.scope,
                " ".join(project.source_titles),
            ]
        ).lower()

        matched_interests = [
            interest for interest in interests if interest and interest in project_text
        ]
        if matched_interests:
            score += min(40, len(matched_interests) * 12)
            reasons.append(
                f"Interest match with {', '.join(matched_interests[:3])}."
            )

        preferred_stack = [
            stack.strip().lower()
            for stack in request_data.preferred_stack
            if stack.strip()
        ]
        project_stack = [stack.strip().lower() for stack in project.tech_stack]
        matched_stack = [stack for stack in preferred_stack if stack in project_stack]
        if matched_stack:
            score += min(30, len(matched_stack) * 10)
            reasons.append(f"Preferred stack includes {', '.join(matched_stack[:3])}.")

        if self._level_matches(request_data.level, project.difficulty):
            score += 20
            reasons.append(
                f"Difficulty '{project.difficulty}' fits a "
                f"{request_data.level.strip().lower()} level profile."
            )

        duration_gap = abs(request_data.duration_months - project.duration_months)
        if duration_gap == 0:
            score += 10
            reasons.append("Duration is an exact match.")
        elif duration_gap <= 2:
            score += 6
            reasons.append("Duration is close to your target timeline.")
        elif duration_gap <= 4:
            score += 3
            reasons.append("Duration is still manageable with planning.")

        score += min(10, project.source_quality_score // 10)
        reasons.append(
            f"Source quality score is {project.source_quality_score}/100 based on discovered paper and repository quality."
        )

        if project.source_status == "real_sources":
            reasons.append("Supported by both a real paper and a real repository.")
        elif project.source_status == "paper_only":
            reasons.append("Grounded in a real research paper.")
        elif project.source_status == "repo_only":
            reasons.append("Grounded in a real implementation repository.")

        score = min(100, score)
        return score, " ".join(reasons)

    def _apply_llm_explanations(
        self,
        recommendations: list[RecommendedProject],
        request_data: AdvisorRecommendationRequest,
    ) -> None:
        improved_explanations = llm_service.rewrite_recommendation_explanations(
            recommendations, request_data
        )
        if not improved_explanations:
            return

        for recommendation, improved_text in zip(
            recommendations, improved_explanations, strict=False
        ):
            recommendation.explanation = improved_text

    def _get_source_candidates(
        self, request_data: AdvisorProjectGenerationRequest
    ) -> SourceSearchResponse:
        arxiv_query_candidates = self._build_arxiv_query_candidates(request_data)
        github_query_candidates = self._build_github_query_candidates(request_data)
        if not arxiv_query_candidates and not github_query_candidates:
            return SourceSearchResponse(papers=[], repositories=[])
        return source_service.search_sources(
            arxiv_query_candidates=arxiv_query_candidates,
            max_results=request_data.max_results,
            github_query_candidates=github_query_candidates,
        )

    def _select_generation_bundles(
        self,
        request_data: AdvisorProjectGenerationRequest,
        sources: SourceSearchResponse,
    ) -> list[GenerationSourceBundle]:
        ranked_papers = self._rank_papers(sources.papers, request_data)
        ranked_repositories = self._rank_repositories(sources.repositories, request_data)
        logger.info(
            "Strong generation sources after filtering: %s papers, %s repositories.",
            len(ranked_papers),
            len(ranked_repositories),
        )

        bundles: list[GenerationSourceBundle] = []
        used_repository_urls: set[str] = set()
        max_results = request_data.max_results

        for paper_score, paper in ranked_papers[:max_results]:
            repository_entry = self._select_repository_for_paper(
                paper=paper,
                paper_score=paper_score,
                ranked_repositories=ranked_repositories,
                request_data=request_data,
                used_repository_urls=used_repository_urls,
            )
            if repository_entry is None:
                bundle = self._create_generation_bundle(
                    request_data=request_data,
                    paper=paper,
                    repository=None,
                    paper_score=paper_score,
                    repository_score=0,
                )
            else:
                repository_score, repository = repository_entry
                used_repository_urls.add(str(repository.url))
                bundle = self._create_generation_bundle(
                    request_data=request_data,
                    paper=paper,
                    repository=repository,
                    paper_score=paper_score,
                    repository_score=repository_score,
                )
            bundles.append(bundle)

        for repository_score, repository in ranked_repositories:
            if len(bundles) >= max_results:
                break
            repository_url = str(repository.url)
            if repository_url in used_repository_urls:
                continue
            bundles.append(
                self._create_generation_bundle(
                    request_data=request_data,
                    paper=None,
                    repository=repository,
                    paper_score=0,
                    repository_score=repository_score,
                )
            )
            used_repository_urls.add(repository_url)

        for index, bundle in enumerate(bundles, start=1):
            logger.info(
                "Generation bundle %s: status=%s paper=%s repo=%s theme=%s",
                index,
                bundle.source_status,
                bundle.paper.title if bundle.paper else None,
                bundle.repository.full_name if bundle.repository else None,
                bundle.theme,
            )

        return bundles[:max_results]

    def _build_selected_sources_from_bundles(
        self, bundles: list[GenerationSourceBundle]
    ) -> SourceSearchResponse:
        papers: list[SourcePaper] = []
        paper_links: set[str] = set()
        repositories: list[SourceRepository] = []
        repository_links: set[str] = set()

        for bundle in bundles:
            if bundle.paper and str(bundle.paper.link) not in paper_links:
                papers.append(bundle.paper)
                paper_links.add(str(bundle.paper.link))
            if bundle.repository and str(bundle.repository.url) not in repository_links:
                repositories.append(bundle.repository)
                repository_links.add(str(bundle.repository.url))

        return SourceSearchResponse(papers=papers, repositories=repositories)

    def _rank_papers(
        self,
        papers: list[SourcePaper],
        request_data: AdvisorProjectGenerationRequest,
    ) -> list[tuple[int, SourcePaper]]:
        ranked: list[tuple[int, SourcePaper]] = []
        threshold = self._paper_score_threshold(request_data)
        for paper in papers:
            score = self._score_paper(paper, request_data)
            if score >= threshold:
                ranked.append((score, paper))
        ranked.sort(key=lambda item: item[0], reverse=True)
        return ranked

    def _rank_repositories(
        self,
        repositories: list[SourceRepository],
        request_data: AdvisorProjectGenerationRequest,
    ) -> list[tuple[int, SourceRepository]]:
        ranked: list[tuple[int, SourceRepository]] = []
        threshold = self._repository_score_threshold(request_data)
        for repository in repositories:
            score = self._score_repository(repository, request_data)
            if score >= threshold:
                ranked.append((score, repository))
        ranked.sort(
            key=lambda item: (item[0], item[1].stars),
            reverse=True,
        )
        return ranked

    def _select_repository_for_paper(
        self,
        paper: SourcePaper,
        paper_score: int,
        ranked_repositories: list[tuple[int, SourceRepository]],
        request_data: AdvisorProjectGenerationRequest,
        used_repository_urls: set[str],
    ) -> tuple[int, SourceRepository] | None:
        best_entry: tuple[int, SourceRepository] | None = None
        best_pair_score = 0

        for repository_score, repository in ranked_repositories:
            repository_url = str(repository.url)
            if repository_url in used_repository_urls:
                continue
            pair_score = self._score_paper_repository_pair(
                paper=paper,
                repository=repository,
                paper_score=paper_score,
                repository_score=repository_score,
                request_data=request_data,
            )
            if pair_score > best_pair_score:
                best_pair_score = pair_score
                best_entry = (repository_score, repository)

        if best_entry is None or best_pair_score < 65:
            return None
        return best_entry

    def _create_generation_bundle(
        self,
        request_data: AdvisorProjectGenerationRequest,
        paper: SourcePaper | None,
        repository: SourceRepository | None,
        paper_score: int,
        repository_score: int,
    ) -> GenerationSourceBundle:
        source_status = self._resolve_source_status(paper, repository)
        source_quality_score = self._combine_source_scores(
            paper_score,
            repository_score,
            source_status,
        )
        return GenerationSourceBundle(
            paper=paper,
            repository=repository,
            source_status=source_status,
            paper_score=paper_score,
            repository_score=repository_score,
            source_quality_score=source_quality_score,
            theme=self._extract_source_theme(request_data, paper, repository),
        )

    def _build_generation_message(
        self,
        generated_projects: list[GeneratedProject],
        repositories_found: int,
    ) -> str:
        generated_count = len(generated_projects)
        if generated_count <= 0:
            return "Real sources were found, but project generation could not produce valid results."
        real_sources_count = sum(
            project.source_status == "real_sources" for project in generated_projects
        )
        paper_only_count = sum(
            project.source_status == "paper_only" for project in generated_projects
        )
        repo_only_count = sum(
            project.source_status == "repo_only" for project in generated_projects
        )
        repo_backed_projects = sum(bool(project.github_link) for project in generated_projects)

        message_parts: list[str] = []
        if real_sources_count:
            message_parts.append(
                f"{real_sources_count} verified project"
                f"{'s' if real_sources_count != 1 else ''}"
            )
        if paper_only_count:
            message_parts.append(
                f"{paper_only_count} paper-backed project"
                f"{'s' if paper_only_count != 1 else ''}"
            )
        if repo_only_count:
            message_parts.append(
                f"{repo_only_count} repo-backed project"
                f"{'s' if repo_only_count != 1 else ''}"
            )

        if len(message_parts) == 1:
            message = f"Generated {message_parts[0]}."
        else:
            message = (
                f"Generated {', '.join(message_parts[:-1])} and {message_parts[-1]}."
            )

        if repositories_found > 0 and repo_backed_projects == 0:
            message += " GitHub repositories were found but did not meet relevance thresholds."
        return message

    def _build_arxiv_query_candidates(
        self, request_data: AdvisorProjectGenerationRequest
    ) -> list[str]:
        interest_keywords = self._normalize_keywords(request_data.interests)
        if not interest_keywords:
            return []

        project_type = self._arxiv_project_type_keyword(request_data.project_type)
        ai_expansion_candidates = self._expand_ai_terms(interest_keywords)
        non_ai_interests = [
            keyword for keyword in interest_keywords if keyword not in {"ai", "llm"}
        ]

        query_candidates = [
            " ".join(interest_keywords),
            *ai_expansion_candidates,
            " ".join(interest_keywords + ([project_type] if project_type else [])),
            " ".join(non_ai_interests or interest_keywords[:1]),
        ]
        return self._deduplicate_queries(query_candidates)

    def _build_github_query_candidates(
        self, request_data: AdvisorProjectGenerationRequest
    ) -> list[str]:
        stack_keywords = self._normalize_keywords(
            self._extend_stack_keywords_for_search(request_data.preferred_stack)
        )
        interest_keywords = self._normalize_keywords(request_data.interests)
        project_type = request_data.project_type.strip().lower()

        query_candidates = [
            " ".join(
                stack_keywords
                + interest_keywords
                + ([project_type] if project_type else [])
            ),
            " ".join(stack_keywords + interest_keywords),
            " ".join(interest_keywords + ([project_type] if project_type else [])),
            "flutter fastapi python project",
        ]
        return self._deduplicate_queries(query_candidates)

    def _expand_ai_terms(self, interest_keywords: list[str]) -> list[str]:
        expanded_queries: list[str] = []
        has_ai = any(keyword in {"ai", "llm"} for keyword in interest_keywords)
        if not has_ai:
            return []

        non_ai_interests = [
            keyword for keyword in interest_keywords if keyword not in {"ai", "llm"}
        ]
        for synonym in ["machine learning", "artificial intelligence"]:
            expanded_queries.append(" ".join([synonym] + non_ai_interests))
        return expanded_queries

    def _arxiv_project_type_keyword(self, project_type: str) -> str:
        normalized = project_type.strip().lower()
        project_type_aliases = {
            "mobile app": "mobile app",
            "web app": "web app",
            "research": "research",
            "tool": "software tool",
            "product": "application",
        }
        return project_type_aliases.get(normalized, normalized)

    def _extend_stack_keywords_for_search(self, preferred_stack: list[str]) -> list[str]:
        stack_keywords = self._normalize_stack_list(preferred_stack)
        extended_keywords: list[str] = []
        stack_aliases = {
            "FastAPI": ["python", "fastapi"],
            "Flutter": ["flutter"],
            "Node.js": ["node.js", "nodejs"],
            "PostgreSQL": ["postgresql"],
            "MongoDB": ["mongodb"],
            "Firebase": ["firebase"],
            "Ollama": ["ollama"],
            "LLM": ["llm"],
        }

        for item in stack_keywords:
            for keyword in stack_aliases.get(item, [item.lower()]):
                if keyword not in extended_keywords:
                    extended_keywords.append(keyword)
        return extended_keywords

    def _build_project_from_payload(
        self,
        payload: dict,
        request_data: AdvisorProjectGenerationRequest,
        project_id: int,
        paper: SourcePaper | None,
        repository: SourceRepository | None,
        variant_index: int,
        used_titles: set[str],
    ) -> GeneratedProject | None:
        source_status = self._resolve_source_status(paper, repository)
        if not source_status:
            return None

        category = self._determine_category(request_data, paper, repository)
        paper_score = self._score_paper(paper, request_data)
        repository_score = self._score_repository(repository, request_data)
        source_quality_score = self._combine_source_scores(
            paper_score, repository_score, source_status
        )

        title = self._clean_generated_title(
            self._safe_string(payload.get("title")),
            request_data=request_data,
            paper=paper,
            repository=repository,
            category=category,
        )
        title = self._ensure_unique_title(
            title,
            request_data=request_data,
            paper=paper,
            repository=repository,
            variant_index=variant_index,
            used_titles=used_titles,
        )
        active_domains = self._active_domain_labels(request_data, paper, repository)
        description = self._clean_cross_domain_leakage(
            self._polish_generated_text(self._safe_string(payload.get("description"))),
            active_domains,
        )
        problem = self._clean_cross_domain_leakage(
            self._polish_generated_text(self._safe_string(payload.get("problem"))),
            active_domains,
        )
        solution = self._clean_cross_domain_leakage(
            self._polish_generated_text(self._safe_string(payload.get("solution"))),
            active_domains,
        )
        if not description or self._has_cross_domain_leakage(description, active_domains):
            description = self._build_description(
                request_data=request_data,
                source_status=source_status,
                source_titles=self._build_source_titles(paper, repository),
                paper=paper,
                repository=repository,
            )
        if not problem or self._has_cross_domain_leakage(problem, active_domains):
            problem = self._build_problem_statement(
                request_data=request_data,
                paper=paper,
                repository=repository,
            )
        if not solution or self._has_cross_domain_leakage(solution, active_domains):
            solution = self._build_solution_statement(
                request_data=request_data,
                paper=paper,
                repository=repository,
            )
        features = self._ensure_length(
            self._safe_string_list(payload.get("features")),
            minimum=3,
            fallback=self._build_features(request_data, paper, repository),
        )
        features = [
            self._clean_cross_domain_leakage(feature, active_domains) for feature in features
        ]
        if any(self._has_cross_domain_leakage(feature, active_domains) for feature in features):
            features = self._build_features(request_data, paper, repository)
        evaluation_metrics = self._ensure_length(
            self._safe_string_list(payload.get("evaluation_metrics")),
            minimum=4,
            fallback=self._build_evaluation_metrics(
                category,
                source_status,
                paper=paper,
                repository=repository,
            ),
        )
        scope = self._safe_string(payload.get("scope"), self._build_scope(request_data))
        if request_data.duration_months <= 1 and "compact MVP" not in scope:
            scope = self._build_scope(request_data)
        architecture_summary = self._safe_string(
            payload.get("architecture_summary"),
            self._build_architecture_summary(
                request_data=request_data,
                repository=repository,
                source_status=source_status,
            ),
        )
        weekly_milestones = self._ensure_length(
            self._safe_string_list(payload.get("weekly_milestones")),
            minimum=4,
            fallback=self._build_weekly_milestones(request_data),
        )
        if request_data.duration_months <= 1:
            weekly_milestones = weekly_milestones[:4]
        risks = self._ensure_length(
            self._safe_string_list(payload.get("risks")),
            minimum=3,
            fallback=self._build_risks(
                source_status,
                repository,
                category=category,
                duration_months=request_data.duration_months,
            ),
        )

        if not all([title, description, problem, solution, scope, architecture_summary]):
            return None

        source_titles = self._build_source_titles(paper, repository)
        resolved_category = self._safe_string(payload.get("category"), category)
        if (
            self._requested_domain_labels(request_data)
            and self._profile_from_category(resolved_category).label == GENERIC_DOMAIN_LABEL
        ):
            resolved_category = category

        try:
            return GeneratedProject(
                id=project_id,
                title=title,
                category=resolved_category,
                difficulty=self._normalize_difficulty(
                    self._safe_string(
                        payload.get("difficulty"),
                        self._difficulty_from_level(request_data.level),
                    )
                ),
                duration_months=max(
                    1,
                    min(
                        24,
                        self._safe_int(payload.get("duration_months"), request_data.duration_months),
                    ),
                ),
                tech_stack=self._build_llm_tech_stack(
                    payload_stack=payload.get("tech_stack"),
                    request_data=request_data,
                    repository=repository,
                ),
                description=description,
                problem=problem,
                solution=solution,
                features=features[: 4 if request_data.duration_months <= 1 else 6],
                evaluation_metrics=evaluation_metrics[:6],
                paper_link=str(paper.link) if paper else None,
                github_link=str(repository.url) if repository else None,
                feasibility_score=max(
                    0,
                    min(
                        100,
                        self._safe_int(
                            payload.get("feasibility_score"),
                            self._calculate_feasibility_score(
                                duration_months=request_data.duration_months,
                                preferred_stack=request_data.preferred_stack,
                                repository=repository,
                                source_status=source_status,
                            ),
                        ),
                    ),
                ),
                scope=scope,
                architecture_summary=architecture_summary,
                weekly_milestones=weekly_milestones,
                risks=risks,
                source_status=source_status,
                source_titles=source_titles,
                source_quality_score=source_quality_score,
                paper_score=paper_score,
                repository_score=repository_score,
            )
        except (ValidationError, ValueError):
            return None

    def _get_paper_for_index(
        self, papers: list[SourcePaper], index: int
    ) -> SourcePaper | None:
        if not papers:
            return None
        return papers[index % len(papers)]

    def _get_repository_for_index(
        self, repositories: list[SourceRepository], index: int
    ) -> SourceRepository | None:
        if not repositories:
            return None
        return repositories[index % len(repositories)]

    def _resolve_source_status(
        self,
        paper: SourcePaper | None,
        repository: SourceRepository | None,
    ) -> str | None:
        has_paper = bool(paper and self._is_real_arxiv_link(str(paper.link)))
        has_repository = bool(
            repository and self._is_real_github_repository_link(str(repository.url))
        )

        if has_paper and has_repository:
            return "real_sources"
        if has_paper:
            return "paper_only"
        if has_repository:
            return "repo_only"
        return None

    def _paper_score_threshold(
        self, request_data: AdvisorProjectGenerationRequest
    ) -> int:
        return 55 if self._requested_domain_labels(request_data) else 45

    def _repository_score_threshold(
        self, request_data: AdvisorProjectGenerationRequest
    ) -> int:
        return 55 if request_data.preferred_stack else 50

    def _domain_alias_map(self) -> dict[str, str]:
        alias_map: dict[str, str] = {}
        for label, profile in DOMAIN_PROFILES.items():
            for alias in (profile.label, *profile.aliases):
                alias_map[self._normalize_text(alias)] = label
        return alias_map

    def _domain_keyword_groups(self) -> dict[str, list[str]]:
        keyword_groups: dict[str, list[str]] = {}
        for label, profile in DOMAIN_PROFILES.items():
            keywords: list[str] = []
            for value in (
                *profile.aliases,
                *profile.target_users,
                *profile.domain_objects,
                *profile.common_workflows,
            ):
                normalized = self._normalize_text(value)
                if normalized and normalized not in keywords:
                    keywords.append(normalized)
            for theme_keywords in profile.theme_keywords.values():
                for value in theme_keywords:
                    normalized = self._normalize_text(value)
                    if normalized and normalized not in keywords:
                        keywords.append(normalized)
            keyword_groups[label] = keywords
        return keyword_groups

    def _infer_domain_label_from_text(self, text: str) -> str:
        normalized_text = self._normalize_text(text)
        if not normalized_text:
            return GENERIC_DOMAIN_LABEL

        best_label = GENERIC_DOMAIN_LABEL
        best_score = 0
        for label, keywords in self._domain_keyword_groups().items():
            if label == GENERIC_DOMAIN_LABEL:
                continue
            score = sum(1 for keyword in keywords if keyword in normalized_text)
            if score > best_score:
                best_label = label
                best_score = score
        return best_label

    def _requested_domain_labels(
        self, request_data: AdvisorProjectGenerationRequest
    ) -> list[str]:
        labels: list[str] = []
        alias_map = self._domain_alias_map()
        for interest in request_data.interests:
            normalized_interest = self._normalize_text(interest)
            label = alias_map.get(normalized_interest)
            if label and label != GENERIC_DOMAIN_LABEL and label not in labels:
                labels.append(label)

        if labels:
            return labels

        inferred_label = self._infer_domain_label_from_text(
            " ".join(request_data.interests + [request_data.prompt_text or ""])
        )
        if inferred_label != GENERIC_DOMAIN_LABEL:
            return [inferred_label]
        return []

    def _source_text(
        self,
        paper: SourcePaper | None,
        repository: SourceRepository | None,
    ) -> str:
        return self._normalize_text(
            " ".join(
                filter(
                    None,
                    [
                        paper.title if paper else "",
                        paper.summary if paper else "",
                        repository.full_name if repository else "",
                        repository.description if repository else "",
                    ],
                )
            )
        )

    def _primary_domain_label(
        self,
        request_data: AdvisorProjectGenerationRequest,
        paper: SourcePaper | None = None,
        repository: SourceRepository | None = None,
    ) -> str:
        requested_labels = self._requested_domain_labels(request_data)
        if requested_labels:
            return requested_labels[0]

        source_label = self._infer_domain_label_from_text(
            self._source_text(paper, repository)
        )
        if source_label != GENERIC_DOMAIN_LABEL:
            return source_label
        return GENERIC_DOMAIN_LABEL

    def _active_domain_labels(
        self,
        request_data: AdvisorProjectGenerationRequest,
        paper: SourcePaper | None = None,
        repository: SourceRepository | None = None,
    ) -> list[str]:
        labels = self._requested_domain_labels(request_data)
        if labels:
            return labels
        primary_label = self._primary_domain_label(request_data, paper, repository)
        return [] if primary_label == GENERIC_DOMAIN_LABEL else [primary_label]

    def _get_domain_profile(
        self,
        request_data: AdvisorProjectGenerationRequest,
        paper: SourcePaper | None = None,
        repository: SourceRepository | None = None,
    ) -> DomainProfile:
        label = self._primary_domain_label(request_data, paper, repository)
        return DOMAIN_PROFILES.get(label, DOMAIN_PROFILES[GENERIC_DOMAIN_LABEL])

    def _profile_from_category(self, category: str) -> DomainProfile:
        normalized_category = self._normalize_text(category)
        if normalized_category:
            inferred = self._infer_domain_label_from_text(normalized_category)
            if inferred in DOMAIN_PROFILES:
                return DOMAIN_PROFILES[inferred]
        return DOMAIN_PROFILES[GENERIC_DOMAIN_LABEL]

    def _count_domain_matches(
        self,
        text: str,
        request_data: AdvisorProjectGenerationRequest,
    ) -> int:
        normalized_text = self._normalize_text(text)
        return sum(
            1
            for label in self._requested_domain_labels(request_data)
            if any(
                keyword in normalized_text
                for keyword in self._domain_keyword_groups().get(label, [])
            )
        )

    def _has_required_domain_match(
        self,
        text: str,
        request_data: AdvisorProjectGenerationRequest,
    ) -> bool:
        requested_domains = self._requested_domain_labels(request_data)
        if not requested_domains:
            return True
        return self._count_domain_matches(text, request_data) > 0

    def _cross_domain_leakage_terms(self, active_domains: list[str]) -> list[str]:
        active = {label for label in active_domains if label != GENERIC_DOMAIN_LABEL}
        if len(active) != 1:
            return []

        blocked_terms: list[str] = []
        for label, profile in DOMAIN_PROFILES.items():
            if label in active or label == GENERIC_DOMAIN_LABEL:
                continue
            for term in profile.leakage_terms:
                normalized = self._normalize_text(term)
                if normalized and normalized not in blocked_terms:
                    blocked_terms.append(normalized)
        return blocked_terms

    def _has_cross_domain_leakage(self, text: str, active_domains: list[str]) -> bool:
        normalized_text = self._normalize_text(text)
        return any(
            re.search(rf"\b{re.escape(term)}\b", normalized_text)
            for term in self._cross_domain_leakage_terms(active_domains)
        )

    def _clean_cross_domain_leakage(
        self, text: str, active_domains: list[str]
    ) -> str:
        if not text:
            return text

        replacements = {
            "patient": "user",
            "doctor": "reviewer",
            "clinical": "domain",
            "healthcare": "domain",
            "medical": "domain",
            "referral": "record",
            "farm": "operations",
            "field": "workflow",
            "crop": "dataset",
            "irrigation": "resource planning",
            "student": "user",
            "teacher": "reviewer",
        }

        cleaned = text
        for term in self._cross_domain_leakage_terms(active_domains):
            cleaned = re.sub(
                rf"\b{re.escape(term)}\b",
                replacements.get(term, "domain"),
                cleaned,
                flags=re.IGNORECASE,
            )
        return re.sub(r"\s+", " ", cleaned).strip()

    def _count_ai_signals(self, text: str) -> int:
        ai_keywords = [
            " ai ",
            "artificial intelligence",
            "machine learning",
            "deep learning",
            "neural",
            "llm",
            "predictive",
            "prediction",
            "model",
        ]
        padded_text = f" {text} "
        return sum(1 for keyword in ai_keywords if keyword in padded_text)

    def _count_stack_matches(
        self,
        text: str,
        request_data: AdvisorProjectGenerationRequest,
    ) -> int:
        if not request_data.preferred_stack:
            return 0
        normalized_stack = self._normalize_keywords(
            self._extend_stack_keywords_for_search(request_data.preferred_stack)
        )
        return sum(1 for keyword in normalized_stack if keyword in text)

    def _count_project_type_matches(
        self,
        text: str,
        request_data: AdvisorProjectGenerationRequest,
    ) -> int:
        project_type = request_data.project_type.strip().lower()
        project_type_keywords = {
            "mobile app": ["mobile", "app", "android", "ios", "flutter"],
            "web app": ["web", "dashboard", "portal", "frontend", "react"],
            "tool": ["tool", "workflow", "platform", "utility"],
            "research": ["research", "study", "analysis"],
            "product": ["app", "platform", "dashboard", "assistant"],
        }
        return sum(
            1
            for keyword in project_type_keywords.get(project_type, [])
            if keyword in text
        )

    def _is_ui_template_repository(self, repository: SourceRepository) -> bool:
        repo_text = self._normalize_text(
            f"{repository.full_name} {repository.description} {repository.language or ''}"
        )
        ui_terms = ["ui", "template", "boilerplate", "clone", "landing page", "portfolio"]
        practical_terms = [
            "api",
            "backend",
            "fastapi",
            "python",
            "doctor",
            "medical",
            "patient",
            "assistant",
            "chatbot",
            "dashboard",
            "diagnosis",
        ]
        return (
            any(term in repo_text for term in ui_terms)
            and not any(term in repo_text for term in practical_terms)
        )

    def _score_paper(
        self,
        paper: SourcePaper | None,
        request_data: AdvisorProjectGenerationRequest,
    ) -> int:
        if paper is None:
            return 0

        paper_text = self._normalize_text(f"{paper.title} {paper.summary}")
        domain_matches = self._count_domain_matches(paper_text, request_data)
        if not self._has_required_domain_match(paper_text, request_data):
            return min(30, self._count_ai_signals(paper_text) * 6)

        score = 35 + min(20, domain_matches * 15)
        score += min(15, self._count_project_type_matches(paper_text, request_data) * 5)

        if self._project_needs_ai(request_data):
            ai_signal_count = self._count_ai_signals(paper_text)
            if ai_signal_count:
                score += min(20, ai_signal_count * 4)
            else:
                score -= 12

        query_keywords = self._normalize_keywords(
            request_data.interests + [request_data.project_type]
        )
        score += min(10, sum(2 for keyword in query_keywords if keyword in paper_text))

        if paper.summary.strip():
            score += 12

        published_year = self._extract_year(paper.published)
        current_year = datetime.utcnow().year
        if published_year >= current_year - 2:
            score += 18
        elif published_year >= current_year - 5:
            score += 12
        elif published_year >= current_year - 8:
            score += 6

        return min(100, score)

    def _score_repository(
        self,
        repository: SourceRepository | None,
        request_data: AdvisorProjectGenerationRequest,
    ) -> int:
        if repository is None:
            return 0

        score = 0
        repo_text = self._normalize_text(
            f"{repository.full_name} {repository.description} {repository.language or ''}"
        )
        if not self._has_required_domain_match(repo_text, request_data):
            return 0

        stars = repository.stars
        if self._is_ui_template_repository(repository):
            return 20 if request_data.project_type.strip().lower() == "ui" else 0

        if stars >= 1000:
            score += 40
        elif stars >= 250:
            score += 30
        elif stars >= 50:
            score += 20
        elif stars >= 10:
            score += 10

        if repository.description.strip():
            score += 15
        if repository.language:
            score += 10
        score += min(20, self._count_domain_matches(repo_text, request_data) * 10)
        score += min(20, self._count_stack_matches(repo_text, request_data) * 6)
        score += min(10, self._count_project_type_matches(repo_text, request_data) * 4)

        if self._project_needs_ai(request_data) and any(
            keyword in repo_text
            for keyword in ["ai", "llm", "chatbot", "model", "prediction", "assistant"]
        ):
            score += 10
        if self._is_mobile_project(request_data) and any(
            keyword in repo_text for keyword in ["flutter", "dart", "mobile", "android", "ios"]
        ):
            score += 12
        if self._project_needs_backend(request_data) and any(
            keyword in repo_text for keyword in ["fastapi", "python", "api", "backend"]
        ):
            score += 10

        return min(100, score)

    def _score_paper_repository_pair(
        self,
        paper: SourcePaper,
        repository: SourceRepository,
        paper_score: int,
        repository_score: int,
        request_data: AdvisorProjectGenerationRequest,
    ) -> int:
        paper_text = self._normalize_text(f"{paper.title} {paper.summary}")
        repo_text = self._normalize_text(
            f"{repository.full_name} {repository.description} {repository.language or ''}"
        )
        profile = self._get_domain_profile(request_data, paper, repository)
        theme_match = int(
            self._extract_source_theme(request_data, paper, None)
            == self._extract_source_theme(request_data, None, repository)
        )
        shared_terms = [
            term
            for term in list(profile.domain_objects[:4]) + list(profile.common_workflows[:4])
            if term in paper_text and term in repo_text
        ]

        pair_score = int((paper_score + repository_score) / 2)
        pair_score += min(14, len(shared_terms) * 4)
        pair_score += self._count_stack_matches(repo_text, request_data) * 3
        pair_score += self._count_project_type_matches(repo_text, request_data) * 2
        if theme_match:
            pair_score += 10
        return min(100, pair_score)

    def _combine_source_scores(
        self,
        paper_score: int,
        repository_score: int,
        source_status: str,
    ) -> int:
        if source_status == "real_sources":
            return min(100, int((paper_score + repository_score) / 2))
        if source_status == "paper_only":
            return paper_score
        return repository_score

    def _build_source_titles(
        self,
        paper: SourcePaper | None,
        repository: SourceRepository | None,
    ) -> list[str]:
        titles: list[str] = []
        if paper:
            titles.append(paper.title)
        if repository:
            titles.append(repository.full_name)
        return titles

    def _extract_source_theme(
        self,
        request_data: AdvisorProjectGenerationRequest,
        paper: SourcePaper | None,
        repository: SourceRepository | None,
    ) -> str:
        profile = self._get_domain_profile(request_data, paper, repository)
        source_text = self._source_text(paper, repository)
        fallback_theme = next(iter(profile.feature_templates.keys()), "general")
        return self._infer_theme_from_text(source_text, fallback_theme, profile)

    def _infer_theme_from_text(
        self,
        source_text: str,
        fallback_theme: str,
        profile: DomainProfile | None = None,
    ) -> str:
        resolved_profile = profile or DOMAIN_PROFILES[GENERIC_DOMAIN_LABEL]
        for theme, keywords in resolved_profile.theme_keywords.items():
            if any(keyword in source_text for keyword in keywords):
                return theme
        return fallback_theme if fallback_theme in resolved_profile.feature_templates else "general"

    def _build_rule_based_title(
        self,
        request_data: AdvisorProjectGenerationRequest,
        paper: SourcePaper | None,
        repository: SourceRepository | None,
        variant_index: int,
    ) -> str:
        profile = self._get_domain_profile(request_data, paper, repository)
        theme = self._extract_source_theme(request_data, paper, repository)
        title_options = list(
            profile.theme_title_nouns.get(
                theme,
                profile.theme_title_nouns.get("general", profile.title_nouns),
            )
        )
        if not title_options:
            title_options = list(profile.title_nouns)

        raw_title = title_options[variant_index % len(title_options)]
        if (
            self._project_needs_ai(request_data)
            and profile.label == GENERIC_DOMAIN_LABEL
            and "AI" not in raw_title.split()
        ):
            raw_title = f"AI {raw_title}"
        return self._finalize_title_candidate(
            raw_title,
            request_data=request_data,
            paper=paper,
            repository=repository,
            category=self._determine_category(request_data, paper, repository),
        )

    def _ensure_unique_title(
        self,
        title: str,
        request_data: AdvisorProjectGenerationRequest,
        paper: SourcePaper | None,
        repository: SourceRepository | None,
        variant_index: int,
        used_titles: set[str],
    ) -> str:
        candidates = [title]
        for offset in range(1, 8):
            candidates.append(
                self._build_rule_based_title(
                    request_data=request_data,
                    paper=paper,
                    repository=repository,
                    variant_index=variant_index + offset,
                )
            )

        for candidate in candidates:
            normalized = candidate.strip().lower()
            if not normalized or normalized in used_titles:
                continue
            used_titles.add(normalized)
            return candidate

        fallback_title = self._build_rule_based_title(
            request_data=request_data,
            paper=paper,
            repository=repository,
            variant_index=variant_index + len(used_titles) + 1,
        )
        used_titles.add(fallback_title.lower())
        return fallback_title

    def _determine_category(
        self,
        request_data: AdvisorProjectGenerationRequest,
        paper: SourcePaper | None,
        repository: SourceRepository | None,
    ) -> str:
        profile = self._get_domain_profile(request_data, paper, repository)
        if profile.label != GENERIC_DOMAIN_LABEL:
            return profile.category
        if self._project_needs_ai(request_data):
            return "AI"
        return request_data.project_type.strip().title() or profile.category

    def _finalize_title_candidate(
        self,
        title: str,
        request_data: AdvisorProjectGenerationRequest,
        paper: SourcePaper | None,
        repository: SourceRepository | None,
        category: str,
    ) -> str:
        profile = self._get_domain_profile(request_data, paper, repository)
        generic_title_blacklist = {
            "project assistant",
            "product project assistant",
            "product workflow dashboard",
            "product patient risk analyzer",
            "workflow dashboard",
            "assistant",
            "dashboard",
        }
        cleaned_title = self._clean_cross_domain_leakage(
            self._format_project_title(title.split()),
            self._active_domain_labels(request_data, paper, repository),
        )
        profile_title_tokens = {
            token.lower()
            for phrase in (*profile.aliases, *profile.title_nouns)
            for token in re.findall(r"[A-Za-z0-9\-]+", phrase)
        }
        if (
            not cleaned_title
            or cleaned_title.lower() in generic_title_blacklist
            or "project assistant" in cleaned_title.lower()
            or cleaned_title.lower().startswith("product ")
            or (
                profile.label != GENERIC_DOMAIN_LABEL
                and not any(
                    token in cleaned_title.lower()
                    for token in profile_title_tokens
                )
            )
        ):
            fallback_noun = profile.title_nouns[0] if profile.title_nouns else "Workflow Tool"
            cleaned_title = self._format_project_title(fallback_noun.split())

        if not self._project_needs_ai(request_data):
            cleaned_title = re.sub(r"\bAI\b\s*", "", cleaned_title).strip()

        if len(cleaned_title.split()) > 8:
            cleaned_title = " ".join(cleaned_title.split()[:8])
        if not cleaned_title:
            cleaned_title = "Source-Backed Workflow Tool"
        return cleaned_title

    def _clean_generated_title(
        self,
        raw_title: str,
        request_data: AdvisorProjectGenerationRequest,
        paper: SourcePaper | None,
        repository: SourceRepository | None,
        category: str,
    ) -> str:
        if not raw_title:
            return self._build_rule_based_title(request_data, paper, repository, 0)

        shortened_title = raw_title.split(" Inspired by ")[0].split(" Based on ")[0].strip()
        tokens = re.findall(r"[A-Za-z0-9\-]+", shortened_title)
        generic_tokens = {"project", "product", "platform", "using", "inspired", "based", "title"}
        cleaned_tokens: list[str] = []
        for token in tokens:
            if token.lower() in generic_tokens and len(tokens) > 3:
                continue
            cleaned_tokens.append(token)
            if len(cleaned_tokens) == 8:
                break

        if len(cleaned_tokens) < 2:
            return self._build_rule_based_title(request_data, paper, repository, 0)

        cleaned_title = self._finalize_title_candidate(
            " ".join(cleaned_tokens),
            request_data=request_data,
            paper=paper,
            repository=repository,
            category=category,
        )
        if len(cleaned_title) > 70 or paper and paper.title.lower() in cleaned_title.lower():
            return self._build_rule_based_title(request_data, paper, repository, 0)
        return cleaned_title

    def _polish_generated_text(self, text: str) -> str:
        replacements = {
            "Build a ai ": "Build an AI ",
            "build a ai ": "build an AI ",
            "Build a AI ": "Build an AI ",
            "source-driven workflow": "core workflow",
            "turning both into a realistic semester scope": "scoping both into a practical graduation project",
        }
        polished = text
        for source, target in replacements.items():
            polished = polished.replace(source, target)
        return re.sub(r"\s+", " ", polished).strip()

    def _format_project_title(self, title_tokens: list[str]) -> str:
        filtered_tokens: list[str] = []
        for token in title_tokens:
            for part in token.split():
                cleaned = re.sub(r"[^A-Za-z0-9\-]+", "", part).strip("-")
                if not cleaned or cleaned.lower() in {item.lower() for item in filtered_tokens}:
                    continue
                filtered_tokens.append(cleaned)
        return " ".join(filtered_tokens[:8]) or "Source-Backed Workflow Tool"

    def _project_type_label(self, request_data: AdvisorProjectGenerationRequest) -> str:
        normalized = request_data.project_type.strip().lower()
        if normalized == "mobile app":
            return "Flutter mobile app"
        if normalized == "web app":
            return "web application"
        if normalized == "tool":
            return "software tool"
        return normalized or "software project"

    def _target_user_summary(self, category: str) -> str:
        profile = self._profile_from_category(category)
        return ", ".join(profile.target_users[:3])

    def _source_backing_note(self, source_status: str) -> str:
        if source_status == "real_sources":
            return "The idea is grounded in a real paper and paired with a practical repository for implementation inspiration."
        if source_status == "paper_only":
            return "The idea is grounded in a real paper and translated into a buildable product scope."
        return "The idea is shaped around a real repository and strengthened with clearer product framing."

    def _build_theme_focus_phrase(self, theme: str, category: str) -> str:
        profile = self._profile_from_category(category)
        return profile.theme_focus.get(
            theme,
            f"{profile.common_workflows[0]} and measurable outcomes"
            if profile.common_workflows
            else f"a practical {category.lower()} workflow with measurable outcomes",
        )

    def _build_theme_problem(
        self,
        theme: str,
        request_data: AdvisorProjectGenerationRequest,
    ) -> str:
        profile = self._get_domain_profile(request_data)
        project_type_label = self._project_type_label(request_data)
        return profile.theme_problems.get(
            theme,
            f"Teams need to turn real source material into a focused {project_type_label} with clear value and realistic scope.",
        )

    def _build_theme_solution(self, theme: str, category: str) -> str:
        profile = self._profile_from_category(category)
        return profile.theme_solutions.get(
            theme,
            f"Focus the product on a practical {category.lower()} workflow with a clear MVP.",
        )

    def _project_action_phrase(
        self,
        category: str,
        request_data: AdvisorProjectGenerationRequest,
        theme: str,
    ) -> str:
        profile = self._profile_from_category(category)
        project_type_label = self._project_type_label(request_data)
        if profile.label == GENERIC_DOMAIN_LABEL and self._project_needs_ai(request_data):
            return f"Create an AI-powered {project_type_label}"
        return f"Create a source-backed {profile.category.lower()} tool"

    def _indefinite_project_phrase(self, category: str, project_type_label: str) -> str:
        normalized_category = category.strip().lower()
        article = "an" if normalized_category[:1] in {"a", "e", "i", "o", "u"} else "a"
        if normalized_category == "ai":
            return f"an AI-powered solution as a {project_type_label}"
        return f"{article} {normalized_category} solution as a {project_type_label}"

    def _is_mobile_project(self, request_data: AdvisorProjectGenerationRequest) -> bool:
        return request_data.project_type.strip().lower() == "mobile app"

    def _project_needs_backend(self, request_data: AdvisorProjectGenerationRequest) -> bool:
        normalized_stack = {item.lower() for item in request_data.preferred_stack}
        project_type = request_data.project_type.strip().lower()
        return bool(
            {"flutter", "react"} & normalized_stack
            or project_type in {"mobile app", "web app", "product", "tool"}
            or self._project_needs_ai(request_data)
        )

    def _project_needs_ai(self, request_data: AdvisorProjectGenerationRequest) -> bool:
        return any(interest.strip().lower() == "ai" for interest in request_data.interests)

    def _difficulty_from_level(self, level: str) -> str:
        normalized_level = self._normalize_level(level)
        difficulty_map = {
            "beginner": "easy",
            "intermediate": "medium",
            "advanced": "hard",
        }
        return difficulty_map.get(normalized_level, "medium")

    def _build_tech_stack(
        self,
        request_data: AdvisorProjectGenerationRequest,
        repository: SourceRepository | None,
    ) -> list[str]:
        stack: list[str] = []
        for item in request_data.preferred_stack:
            cleaned = item.strip()
            if cleaned and cleaned not in stack:
                stack.append(cleaned)

        if self._is_mobile_project(request_data) and "Flutter" not in stack:
            stack.append("Flutter")
        if "Flutter" in stack and "Dart" not in stack:
            stack.append("Dart")
        if self._project_needs_backend(request_data) and "FastAPI" not in stack:
            stack.append("FastAPI")
        if self._project_needs_ai(request_data) and "Python" not in stack:
            stack.append("Python")

        if repository and repository.language and repository.language not in stack:
            stack.append(repository.language)

        return stack[:6]

    def _build_llm_tech_stack(
        self,
        payload_stack: object,
        request_data: AdvisorProjectGenerationRequest,
        repository: SourceRepository | None,
    ) -> list[str]:
        stack = self._normalize_stack_list(self._safe_string_list(payload_stack))
        base_stack = self._build_tech_stack(request_data, repository)
        if not stack:
            return self._build_tech_stack(request_data, repository)

        merged_stack: list[str] = []
        for item in base_stack + stack:
            if item not in merged_stack:
                merged_stack.append(item)
        return merged_stack[:6]

    def _build_description(
        self,
        request_data: AdvisorProjectGenerationRequest,
        source_status: str,
        source_titles: list[str],
        paper: SourcePaper | None,
        repository: SourceRepository | None,
    ) -> str:
        profile = self._get_domain_profile(request_data, paper, repository)
        category = self._determine_category(request_data, paper, repository)
        project_type_label = self._project_type_label(request_data)
        target_user = ", ".join(profile.target_users[:2])
        stack_text = ", ".join(self._build_tech_stack(request_data, repository)[:4])
        source_note = self._source_backing_note(source_status)
        theme = self._extract_source_theme(request_data, paper, repository)
        focus_phrase = self._build_theme_focus_phrase(theme, category)
        workflow_phrase = (
            profile.common_workflows[0] if profile.common_workflows else "a practical workflow"
        )
        mvp_phrase = (
            "compact MVP"
            if request_data.duration_months <= 1
            else "practical graduation-project MVP"
        )
        description = (
            f"Create a source-backed {profile.category.lower()} tool for {target_user}. "
            f"It supports {workflow_phrase}, with a focus on {focus_phrase}. "
            f"It uses {stack_text} for a {mvp_phrase}. "
            f"{source_note}"
        )
        return self._clean_cross_domain_leakage(
            description,
            self._active_domain_labels(request_data, paper, repository),
        )

    def _build_problem_statement(
        self,
        request_data: AdvisorProjectGenerationRequest,
        paper: SourcePaper | None,
        repository: SourceRepository | None,
    ) -> str:
        profile = self._get_domain_profile(request_data, paper, repository)
        interest_text = ", ".join(request_data.interests)
        theme = self._extract_source_theme(request_data, paper, repository)
        theme_problem = self._build_theme_problem(theme, request_data)
        compact_note = (
            " The scope should stay compact and centered on one core workflow."
            if request_data.duration_months <= 1
            else ""
        )
        if paper and repository:
            problem = (
                f"Students interested in {interest_text} need a project that is academically grounded and still practical to implement. "
                f"{theme_problem} The paper provides the research direction, while the repository shows a usable implementation pattern for the same workflow."
            )
        elif paper:
            problem = (
                f"Students interested in {interest_text} need a way to turn the paper's core idea into a usable software product with measurable outcomes and a clear engineering scope. "
                f"{theme_problem}"
            )
        else:
            problem = (
                f"Students interested in {interest_text} need a project that turns the repository's implementation direction into a cleaner product with stronger academic framing and evaluation criteria. "
                f"{theme_problem}"
            )
        return self._clean_cross_domain_leakage(
            f"{problem}{compact_note}",
            self._active_domain_labels(request_data, paper, repository),
        )

    def _build_solution_statement(
        self,
        request_data: AdvisorProjectGenerationRequest,
        paper: SourcePaper | None,
        repository: SourceRepository | None,
    ) -> str:
        category = self._determine_category(request_data, paper, repository)
        project_type_label = self._project_type_label(request_data)
        stack_text = ", ".join(self._build_tech_stack(request_data, repository)[:4])
        theme = self._extract_source_theme(request_data, paper, repository)
        solution_focus = self._build_theme_solution(theme, category)
        compact_note = (
            " Keep the scope as a compact MVP with 3 to 4 core features."
            if request_data.duration_months <= 1
            else ""
        )
        if paper and repository:
            solution = (
                f"Create {self._indefinite_project_phrase(category, project_type_label)} using {stack_text}. "
                f"{solution_focus} Use the paper as research grounding and the repository as implementation inspiration."
            )
        elif paper:
            solution = (
                f"Create {self._indefinite_project_phrase(category, project_type_label)} using {stack_text}. "
                f"{solution_focus} Use the paper to guide the core workflow, data flow, and evaluation plan."
            )
        else:
            solution = (
                f"Create {self._indefinite_project_phrase(category, project_type_label)} using {stack_text}. "
                f"{solution_focus} Use the repository as implementation inspiration, then refine the workflow, metrics, and product framing for graduation-project quality."
            )
        return self._clean_cross_domain_leakage(
            f"{solution}{compact_note}",
            self._active_domain_labels(request_data, paper, repository),
        )

    def _build_features(
        self,
        request_data: AdvisorProjectGenerationRequest,
        paper: SourcePaper | None,
        repository: SourceRepository | None,
    ) -> list[str]:
        profile = self._get_domain_profile(request_data, paper, repository)
        theme = self._extract_source_theme(request_data, paper, repository)
        features = list(
            profile.feature_templates.get(
                theme,
                profile.feature_templates.get("general", ()),
            )
        )
        features = [
            self._clean_cross_domain_leakage(
                feature,
                self._active_domain_labels(request_data, paper, repository),
            )
            for feature in features
        ]
        max_features = 4 if request_data.duration_months <= 1 else 6
        return features[:max_features]

    def _build_evaluation_metrics(
        self,
        category: str,
        source_status: str,
        paper: SourcePaper | None = None,
        repository: SourceRepository | None = None,
    ) -> list[str]:
        profile = self._profile_from_category(category)
        theme = self._infer_theme_from_text(
            self._source_text(paper, repository),
            fallback_theme="general",
            profile=profile,
        )
        metrics = list(
            profile.metric_templates.get(
                theme,
                profile.metric_templates.get("general", ()),
            )
        )
        if source_status == "paper_only":
            metrics.append("Research grounding quality")
        elif source_status == "repo_only":
            metrics.append("Implementation adaptation quality")
        else:
            metrics.append("Research-to-implementation alignment")
        return metrics[:6]

    def _build_scope(self, request_data: AdvisorProjectGenerationRequest) -> str:
        if request_data.duration_months <= 1:
            return (
                "1-month compact MVP focused on one core workflow, a lightweight backend API, "
                "a minimal client or dashboard flow, and measurable evaluation."
            )
        if request_data.duration_months <= 3:
            return (
                f"{request_data.duration_months}-month limited MVP with a focused backend API, "
                "practical client workflow, and measurable evaluation plan."
            )
        return (
            f"{request_data.duration_months}-month project with a clear MVP, backend API, "
            "client interface, source-based core module, and measurable evaluation plan."
        )

    def _build_architecture_summary(
        self,
        request_data: AdvisorProjectGenerationRequest,
        repository: SourceRepository | None,
        source_status: str,
    ) -> str:
        repository_note = (
            f" The implementation can reuse structural ideas from {repository.full_name}."
            if repository
            else ""
        )
        if request_data.duration_months <= 1:
            return (
                "Use a compact client or admin view connected to a FastAPI backend with one focused domain service, "
                "simple storage, and a small reporting endpoint for the core workflow."
                f"{repository_note} Source status: {source_status}."
            )
        return (
            "Use a client application connected to a FastAPI backend with service-based business logic, "
            "source ingestion utilities, domain processing modules, and analytics or reporting endpoints."
            f"{repository_note} Source status: {source_status}."
        )

    def _build_weekly_milestones(
        self,
        request_data: AdvisorProjectGenerationRequest,
    ) -> list[str]:
        if request_data.duration_months <= 1:
            return [
                "Week 1: Finalize the compact MVP scope, source review, and evaluation targets",
                "Week 2: Build the core backend API and data flow",
                "Week 3: Implement the main workflow and one minimal dashboard or client view",
                "Week 4: Test, refine, and prepare the final demo and documentation",
            ]

        milestone_count = min(max(request_data.duration_months, 4), 8)
        base_milestones = [
            "Week 1: Finalize problem statement, source review, and scope",
            "Week 2: Design system architecture and API contracts",
            "Week 3: Build core backend services and data models",
            "Week 4: Implement main workflow and source-driven logic",
            "Week 5: Develop client screens or dashboard flows",
            "Week 6: Add evaluation, testing, and refinement",
            "Week 7: Improve UX, documentation, and supervisor feedback changes",
            "Week 8: Prepare final validation, demo, and presentation materials",
        ]
        return base_milestones[:milestone_count]

    def _build_risks(
        self,
        source_status: str,
        repository: SourceRepository | None,
        category: str = "",
        duration_months: int = 0,
    ) -> list[str]:
        profile = self._profile_from_category(category) if category else DOMAIN_PROFILES[GENERIC_DOMAIN_LABEL]
        risks = list(profile.risk_templates[:3]) or [
            "Scope may expand if feature priorities are not controlled early.",
            "Evaluation quality depends on having realistic testing scenarios.",
        ]
        if duration_months <= 1:
            risks.append(
                "Limited time for advanced ML or a full dashboard means the team should keep the compact MVP focused on one core workflow."
            )
        if source_status == "paper_only":
            risks.append(
                "Research concepts may require simplification before they fit the available implementation time."
            )
        elif source_status == "repo_only":
            risks.append(
                "Repository code may not map directly to the desired academic scope and may need refactoring."
            )
        else:
            risks.append(
                "Aligning research ideas with repository implementation details may require additional design tradeoffs."
            )
        if repository and repository.language:
            risks.append(
                f"The team may need extra ramp-up time if {repository.language} is not already familiar."
            )
        return risks[:5]

    def _calculate_feasibility_score(
        self,
        duration_months: int,
        preferred_stack: list[str],
        repository: SourceRepository | None,
        source_status: str,
    ) -> int:
        score = 62 if duration_months <= 1 else 68
        if duration_months >= 5:
            score += 10
        elif duration_months <= 1:
            score += 4
        if preferred_stack:
            score += 8
        if repository and repository.stars >= 100:
            score += 6
        if repository and repository.language:
            score += 4
        if source_status == "real_sources":
            score += 7
        return min(95, score)

    def _build_target_users(self, project: GeneratedProject) -> list[str]:
        profile = self._profile_from_category(project.category)
        return [user.title() for user in profile.target_users[:3]]

    def _build_backend_modules(self, project: GeneratedProject) -> list[str]:
        return [
            "Authentication and user management",
            "Project domain service layer",
            "Source processing and scoring module",
            "Reporting and analytics module",
            "API routing and validation layer",
        ]

    def _build_flutter_screens(self, project: GeneratedProject) -> list[str]:
        return [
            "Splash and onboarding screen",
            "Login and profile screen",
            "Dashboard screen",
            "Main workflow screen",
            "Reports or analytics screen",
            "Settings and feedback screen",
        ]

    def _build_storage_plan(self, project: GeneratedProject) -> str:
        return (
            "Use in-memory storage for the current backend demo. For production or future work, "
            "replace it with PostgreSQL for core entities and object storage for uploaded assets if needed."
        )

    def _build_api_endpoints(self, project: GeneratedProject) -> list[str]:
        return [
            "POST /auth/login",
            "GET /dashboard/summary",
            "POST /workflow/run",
            "GET /reports",
            "POST /feedback",
        ]

    def _build_ai_pipeline(self, project: GeneratedProject) -> str:
        if project.category.lower() == "ai":
            return (
                "Collect inputs, preprocess them, run inference or scoring, store outputs, "
                "and expose prediction summaries through the API."
            )
        return "AI is optional. If used, apply lightweight scoring or recommendation logic inside a dedicated service module."

    def _build_presentation_outline(self, project: GeneratedProject) -> list[str]:
        return [
            "Problem background and motivation",
            "Objectives and target users",
            "System architecture and modules",
            "Key features and workflow",
            "Implementation plan and milestones",
            "Evaluation metrics and risks",
            "Future work and conclusion",
        ]

    def _build_source_links(self, project: GeneratedProject) -> list[str]:
        links: list[str] = []
        if project.paper_link:
            links.append(project.paper_link)
        if project.github_link:
            links.append(project.github_link)
        return links

    def _build_project_markdown(self, project: GeneratedProject | None) -> str:
        if project is None:
            return ""
        source_lines = self._format_source_lines(project.paper_link, project.github_link)
        return "\n".join(
            [
                f"# {project.title}",
                "",
                "## Problem",
                project.problem,
                "",
                "## Solution",
                project.solution,
                "",
                "## Scope",
                project.scope,
                "",
                "## Architecture",
                project.architecture_summary,
                "",
                "## Features",
                *[f"- {feature}" for feature in project.features],
                "",
                "## Weekly Milestones",
                *[f"- {milestone}" for milestone in project.weekly_milestones],
                "",
                "## Evaluation Metrics",
                *[f"- {metric}" for metric in project.evaluation_metrics],
                "",
                "## Risks",
                *[f"- {risk}" for risk in project.risks],
                "",
                "## Source Links",
                *source_lines,
            ]
        )

    def _build_blueprint_markdown(self, blueprint: ProjectBlueprint) -> str:
        return "\n".join(
            [
                f"# {blueprint.project_title}",
                "",
                "## Problem",
                blueprint.refined_problem_statement,
                "",
                "## Objectives",
                *[f"- {item}" for item in blueprint.objectives],
                "",
                "## Target Users",
                *[f"- {item}" for item in blueprint.target_users],
                "",
                "## Core Features",
                *[f"- {item}" for item in blueprint.core_features],
                "",
                "## Optional Features",
                *[f"- {item}" for item in blueprint.optional_features],
                "",
                "## Architecture",
                blueprint.system_architecture,
                "",
                "## Backend Modules",
                *[f"- {item}" for item in blueprint.backend_modules],
                "",
                "## Flutter Screens",
                *[f"- {item}" for item in blueprint.flutter_screens],
                "",
                "## Storage Plan",
                blueprint.database_or_storage_plan,
                "",
                "## API Endpoints",
                *[f"- {item}" for item in blueprint.api_endpoints],
                "",
                "## AI Pipeline",
                blueprint.ai_pipeline,
                "",
                "## Weekly Milestones",
                *[f"- {item}" for item in blueprint.weekly_milestones],
                "",
                "## Evaluation Metrics",
                *[f"- {item}" for item in blueprint.evaluation_metrics],
                "",
                "## Risks",
                *[f"- {item}" for item in blueprint.risks],
                "",
                "## Source Links",
                *[f"- {item}" for item in blueprint.source_links],
            ]
        )

    def _format_source_lines(
        self, paper_link: str | None, github_link: str | None
    ) -> list[str]:
        lines: list[str] = []
        if paper_link:
            lines.append(f"- arXiv paper: {paper_link}")
        if github_link:
            lines.append(f"- GitHub repository: {github_link}")
        if not lines:
            lines.append("- No source links available")
        return lines

    def _level_matches(self, level: str, difficulty: str) -> bool:
        normalized_level = self._normalize_level(level)
        normalized_difficulty = self._normalize_difficulty(difficulty)

        level_to_difficulty = {
            "beginner": {"easy"},
            "intermediate": {"easy", "medium"},
            "advanced": {"medium", "hard"},
        }
        return normalized_difficulty in level_to_difficulty.get(
            normalized_level, {"easy", "medium", "hard"}
        )

    def _normalize_level(self, level: str) -> str:
        value = level.strip().lower()
        aliases = {
            "easy": "beginner",
            "junior": "beginner",
            "entry": "beginner",
            "entry-level": "beginner",
            "مبتدئ": "beginner",
            "سهل": "beginner",
            "medium": "intermediate",
            "mid": "intermediate",
            "mid-level": "intermediate",
            "متوسط": "intermediate",
            "senior": "advanced",
            "expert": "advanced",
            "hard": "advanced",
            "صعب": "advanced",
            "متقدم": "advanced",
        }
        return aliases.get(value, value)

    def _normalize_difficulty(self, difficulty: str) -> str:
        value = difficulty.strip().lower()
        aliases = {
            "beginner": "easy",
            "entry": "easy",
            "entry-level": "easy",
            "intermediate": "medium",
            "mid": "medium",
            "mid-level": "medium",
            "advanced": "hard",
            "expert": "hard",
        }
        return aliases.get(value, value)

    def _is_real_arxiv_link(self, link: str) -> bool:
        return "arxiv.org" in link and "/search" not in link and "/abs/" in link

    def _is_real_github_repository_link(self, link: str) -> bool:
        return (
            "github.com/" in link
            and "/search" not in link
            and len(link.rstrip("/").split("/")) >= 5
        )

    def _extract_year(self, published: str) -> int:
        try:
            return int(published[:4])
        except (TypeError, ValueError):
            return 0

    def _safe_string(self, value: object, default: str = "") -> str:
        if isinstance(value, str):
            return value.strip()
        return default

    def _safe_string_list(self, value: object) -> list[str]:
        if not isinstance(value, list):
            return []
        items = [item.strip() for item in value if isinstance(item, str) and item.strip()]
        unique_items: list[str] = []
        for item in items:
            if item not in unique_items:
                unique_items.append(item)
        return unique_items

    def _safe_int(self, value: object, default: int) -> int:
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        return default

    def _coerce_duration(self, value: object) -> int | None:
        if isinstance(value, int):
            duration = value
        elif isinstance(value, float):
            duration = int(value)
        else:
            return None

        if 1 <= duration <= 24:
            return duration
        return None

    def _coerce_team_size(self, value: object) -> int | None:
        if isinstance(value, int):
            team_size = value
        elif isinstance(value, float):
            team_size = int(value)
        else:
            return None

        if 1 <= team_size <= 10:
            return team_size
        return None

    def _canonicalize_level(self, level: str) -> str:
        normalized = self._normalize_level(level) if level.strip() else ""
        if normalized in {"beginner", "intermediate", "advanced"}:
            return normalized
        return ""

    def _canonicalize_project_type(self, project_type: str) -> str:
        normalized = project_type.strip().lower()
        project_type_aliases = {
            "mobile": "mobile app",
            "app": "mobile app",
            "application": "mobile app",
            "web": "web app",
            "website": "web app",
            "research-based": "research",
        }
        if not normalized:
            return ""
        return project_type_aliases.get(normalized, normalized)

    def _normalize_interest_values(self, interests: list[str]) -> list[str]:
        normalized: list[str] = []
        for interest in interests:
            cleaned = interest.strip()
            if not cleaned:
                continue
            canonical = cleaned
            lowered = cleaned.lower()
            for label, keywords in INTEREST_KEYWORDS.items():
                if lowered == label.lower() or lowered in keywords:
                    canonical = label
                    break
            if canonical not in normalized:
                normalized.append(canonical)
        return normalized

    def _normalize_stack_list(self, preferred_stack: list[str]) -> list[str]:
        normalized: list[str] = []
        for item in preferred_stack:
            cleaned = item.strip()
            if not cleaned:
                continue
            canonical = cleaned
            lowered = cleaned.lower()
            for label, keywords in STACK_KEYWORDS.items():
                if lowered == label.lower() or lowered in keywords:
                    canonical = label
                    break
            if canonical not in normalized:
                normalized.append(canonical)
        return normalized

    def _apply_generation_defaults(
        self, preferences: ParsedPreferences, prompt_text: str
    ) -> ParsedPreferences:
        interests = preferences.interests[:]
        if not interests:
            fallback_interest_map = {
                "health": "Healthcare",
                "medical": "Healthcare",
                "education": "Education",
                "student": "Education",
                "finance": "Finance",
                "legal": "Legal",
                "law": "Legal",
                "construction": "Construction",
                "security": "Cybersecurity",
                "commerce": "E-commerce",
                "shopping": "E-commerce",
                "ai": "AI",
                "llm": "AI",
            }
            normalized_prompt = self._normalize_text(prompt_text)
            for keyword, label in fallback_interest_map.items():
                if keyword in normalized_prompt:
                    interests.append(label)
                    break
        if not interests and preferences.preferred_stack:
            if any(item in {"Ollama", "LLM"} for item in preferences.preferred_stack):
                interests.append("AI")
        if not interests:
            interests.append("Software Engineering")

        constraints = [
            item
            for item in self._safe_string_list(preferences.constraints)
            if not item.startswith("Build as a ")
            and not item.startswith("Target difficulty: ")
            and not item.startswith("Finish within ")
            and not item.startswith("Team size: ")
        ]
        if preferences.project_type:
            constraints.append(f"Build as a {preferences.project_type}")
        if preferences.level:
            constraints.append(f"Target difficulty: {preferences.level}")
        if preferences.duration_months is not None:
            constraints.append(f"Finish within {preferences.duration_months} months")
        if preferences.team_size is not None:
            constraints.append(f"Team size: {preferences.team_size}")

        return ParsedPreferences(
            interests=interests,
            level=preferences.level or "intermediate",
            duration_months=preferences.duration_months or 6,
            preferred_stack=preferences.preferred_stack,
            project_type=preferences.project_type or "product",
            constraints=constraints,
            team_size=preferences.team_size,
            source=preferences.source,
        )

    def _normalize_keywords(self, keywords: list[str]) -> list[str]:
        normalized: list[str] = []
        for keyword in keywords:
            cleaned = keyword.strip().lower()
            if cleaned and cleaned not in normalized:
                normalized.append(cleaned)
        return normalized

    def _deduplicate_queries(self, queries: list[str]) -> list[str]:
        unique_queries: list[str] = []
        seen: set[str] = set()

        for query in queries:
            normalized_query = " ".join(query.split())
            if not normalized_query or normalized_query in seen:
                continue
            seen.add(normalized_query)
            unique_queries.append(normalized_query)

        return unique_queries

    def _ensure_length(
        self,
        items: list[str],
        minimum: int,
        fallback: list[str],
    ) -> list[str]:
        if len(items) >= minimum:
            return items
        merged: list[str] = []
        for item in items + fallback:
            if item not in merged:
                merged.append(item)
        return merged


advisor_service = AdvisorService()
