from app.schemas.advisor_schema import ChatSessionDetailResponse, ChatSessionResponse
from app.schemas.user_schema import MessageResponse
from app.services.chat_service import chat_service


def list_chat_sessions(user_id: int | None = None) -> list[ChatSessionResponse]:
    return chat_service.list_sessions(user_id)


def get_chat_session(session_id: int) -> ChatSessionDetailResponse:
    return chat_service.get_session(session_id)


def delete_chat_session(session_id: int) -> MessageResponse:
    payload = chat_service.delete_session(session_id)
    return MessageResponse(**payload)
