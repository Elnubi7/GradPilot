from app.schemas.user_schema import (
    FavoriteCreateRequest,
    FavoriteResponse,
    MessageResponse,
    UserLoginRequest,
    UserLoginResponse,
    UserRegisterRequest,
    UserResponse,
    UserUpdateRequest,
)
from app.services.user_service import user_service


def register_user(request_data: UserRegisterRequest) -> UserResponse:
    return user_service.register_user(request_data)


def login_user(request_data: UserLoginRequest) -> UserLoginResponse:
    return user_service.login_user(request_data)


def list_users() -> list[UserResponse]:
    return user_service.list_users()


def get_user(user_id: int) -> UserResponse:
    return user_service.get_user(user_id)


def update_user(user_id: int, request_data: UserUpdateRequest) -> UserResponse:
    return user_service.update_user(user_id, request_data)


def delete_user(user_id: int) -> MessageResponse:
    return user_service.delete_user(user_id)


def create_favorite(request_data: FavoriteCreateRequest) -> FavoriteResponse:
    return user_service.create_favorite(request_data)


def list_favorites(user_id: int | None = None) -> list[FavoriteResponse]:
    return user_service.list_favorites(user_id)


def delete_favorite(favorite_id: int) -> MessageResponse:
    return user_service.delete_favorite(favorite_id)
