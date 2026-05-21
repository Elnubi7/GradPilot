import logging

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.db.database import SessionLocal
from app.db.models import ChatMessage, ChatSession
from app.schemas.advisor_schema import (
    ChatMessageResponse,
    ChatSessionDetailResponse,
    ChatSessionResponse,
    GeneratedProject,
    ProjectChatMessage,
)


logger = logging.getLogger(__name__)


class ChatService:
    def persist_chat_exchange(
        self,
        project: GeneratedProject,
        messages: list[ProjectChatMessage],
        reply: str,
        user_id: int | None = None,
        session_id: int | None = None,
    ) -> int | None:
        if not settings.enable_database:
            return None

        latest_user_message = self._get_latest_user_message(messages)
        try:
            with SessionLocal() as db:
                if session_id is not None:
                    session = db.get(ChatSession, session_id)
                    if session is None:
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Chat session with id {session_id} not found.",
                        )
                else:
                    session = ChatSession(
                        user_id=user_id,
                        project_id=project.id,
                        title=project.title,
                        project_snapshot=project.model_dump(),
                    )
                    db.add(session)
                    db.flush()

                if latest_user_message:
                    db.add(
                        ChatMessage(
                            session_id=session.id,
                            role="user",
                            content=latest_user_message,
                        )
                    )
                db.add(
                    ChatMessage(
                        session_id=session.id,
                        role="assistant",
                        content=reply,
                    )
                )
                db.commit()
                return session.id
        except SQLAlchemyError as exc:
            logger.warning("Chat persistence unavailable; returning non-persistent reply: %s", exc)
            return None

    def list_sessions(self, user_id: int | None = None) -> list[ChatSessionResponse]:
        self._require_database()
        with SessionLocal() as db:
            statement = select(ChatSession).order_by(ChatSession.id.desc())
            if user_id is not None:
                statement = statement.where(ChatSession.user_id == user_id)
            sessions = db.scalars(statement).all()
            return [self._to_session_response(session) for session in sessions]

    def get_session(self, session_id: int) -> ChatSessionDetailResponse:
        self._require_database()
        with SessionLocal() as db:
            session = db.get(ChatSession, session_id)
            if session is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Chat session with id {session_id} not found.",
                )
            return self._to_session_detail_response(session)

    def delete_session(self, session_id: int) -> dict[str, str]:
        self._require_database()
        with SessionLocal() as db:
            session = db.get(ChatSession, session_id)
            if session is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Chat session with id {session_id} not found.",
                )
            db.delete(session)
            db.commit()
            return {"message": "Chat session deleted successfully."}

    def _get_latest_user_message(self, messages: list[ProjectChatMessage]) -> str:
        for message in reversed(messages):
            if message.role == "user" and message.content.strip():
                return message.content.strip()
        return ""

    def _to_session_response(self, session: ChatSession) -> ChatSessionResponse:
        return ChatSessionResponse(
            id=session.id,
            user_id=session.user_id,
            project_id=session.project_id,
            title=session.title,
            project_snapshot=session.project_snapshot or {},
            created_at=session.created_at,
        )

    def _to_session_detail_response(
        self, session: ChatSession
    ) -> ChatSessionDetailResponse:
        return ChatSessionDetailResponse(
            **self._to_session_response(session).model_dump(),
            messages=[
                ChatMessageResponse(
                    id=message.id,
                    session_id=message.session_id,
                    role=message.role,
                    content=message.content,
                    created_at=message.created_at,
                )
                for message in session.messages
            ],
        )

    def _require_database(self) -> None:
        if not settings.enable_database:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database persistence is disabled.",
            )


chat_service = ChatService()
