from fastapi import APIRouter, Query

from app.controllers.chat_controller import (
    delete_chat_session,
    get_chat_session,
    list_chat_sessions,
)
from app.schemas.advisor_schema import ChatSessionDetailResponse, ChatSessionResponse
from app.schemas.user_schema import MessageResponse


router = APIRouter()


@router.get("/sessions", response_model=list[ChatSessionResponse])
def list_chat_sessions_route(
    user_id: int | None = Query(default=None)
) -> list[ChatSessionResponse]:
    return list_chat_sessions(user_id)


@router.get("/sessions/{session_id}", response_model=ChatSessionDetailResponse)
def get_chat_session_route(session_id: int) -> ChatSessionDetailResponse:
    return get_chat_session(session_id)


@router.delete("/sessions/{session_id}", response_model=MessageResponse)
def delete_chat_session_route(session_id: int) -> MessageResponse:
    return delete_chat_session(session_id)
