from fastapi import APIRouter, Query, status

from app.controllers.user_controller import (
    create_favorite,
    delete_favorite,
    delete_user,
    get_user,
    list_favorites,
    list_users,
    login_user,
    register_user,
    update_user,
)
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


router = APIRouter()


@router.post("/users/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED, tags=["Users"])
def register_user_route(request_data: UserRegisterRequest) -> UserResponse:
    return register_user(request_data)


@router.post("/users/login", response_model=UserLoginResponse, tags=["Users"])
def login_user_route(request_data: UserLoginRequest) -> UserLoginResponse:
    return login_user(request_data)


@router.get("/users", response_model=list[UserResponse], tags=["Users"])
def list_users_route() -> list[UserResponse]:
    return list_users()


@router.get("/users/{user_id}", response_model=UserResponse, tags=["Users"])
def get_user_route(user_id: int) -> UserResponse:
    return get_user(user_id)


@router.put("/users/{user_id}", response_model=UserResponse, tags=["Users"])
def update_user_route(user_id: int, request_data: UserUpdateRequest) -> UserResponse:
    return update_user(user_id, request_data)


@router.delete("/users/{user_id}", response_model=MessageResponse, tags=["Users"])
def delete_user_route(user_id: int) -> MessageResponse:
    return delete_user(user_id)


@router.post("/favorites", response_model=FavoriteResponse, status_code=status.HTTP_201_CREATED, tags=["Favorites"])
def create_favorite_route(request_data: FavoriteCreateRequest) -> FavoriteResponse:
    return create_favorite(request_data)


@router.get("/favorites", response_model=list[FavoriteResponse], tags=["Favorites"])
def list_favorites_route(user_id: int | None = Query(default=None)) -> list[FavoriteResponse]:
    return list_favorites(user_id)


@router.delete("/favorites/{favorite_id}", response_model=MessageResponse, tags=["Favorites"])
def delete_favorite_route(favorite_id: int) -> MessageResponse:
    return delete_favorite(favorite_id)
