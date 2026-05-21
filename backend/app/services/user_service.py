from fastapi import HTTPException, status
from sqlalchemy import select

from app.core.config import settings
from app.db.database import SessionLocal
from app.db.models import Favorite, SavedProject, User
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


class UserService:
    def register_user(self, request_data: UserRegisterRequest) -> UserResponse:
        self._require_database()
        with SessionLocal() as db:
            existing_user = db.scalars(
                select(User).where(User.email == request_data.email)
            ).first()
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already exists.",
                )

            new_user = User(**request_data.model_dump())
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            return self._to_user_response(new_user)

    def login_user(self, request_data: UserLoginRequest) -> UserLoginResponse:
        self._require_database()
        with SessionLocal() as db:
            user = db.scalars(
                select(User).where(User.email == request_data.email.strip().lower())
            ).first()
            if user is None or user.password != request_data.password:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password.",
                )

            return UserLoginResponse(
                success=True,
                user=self._to_user_response(user),
                message="Login successful",
            )

    def list_users(self) -> list[UserResponse]:
        self._require_database()
        with SessionLocal() as db:
            users = db.scalars(select(User).order_by(User.id)).all()
            return [self._to_user_response(user) for user in users]

    def get_user(self, user_id: int) -> UserResponse:
        self._require_database()
        with SessionLocal() as db:
            user = self._find_user(db, user_id)
            return self._to_user_response(user)

    def update_user(self, user_id: int, request_data: UserUpdateRequest) -> UserResponse:
        self._require_database()
        with SessionLocal() as db:
            user = self._find_user(db, user_id)
            update_data = request_data.model_dump(exclude_unset=True)

            if "email" in update_data:
                duplicate_user = db.scalars(
                    select(User).where(
                        User.email == update_data["email"],
                        User.id != user_id,
                    )
                ).first()
                if duplicate_user:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Email already exists.",
                    )

            for key, value in update_data.items():
                setattr(user, key, value)

            db.commit()
            db.refresh(user)
            return self._to_user_response(user)

    def delete_user(self, user_id: int) -> MessageResponse:
        self._require_database()
        with SessionLocal() as db:
            user = self._find_user(db, user_id)
            db.delete(user)
            db.commit()
            return MessageResponse(message="User deleted successfully.")

    def create_favorite(self, request_data: FavoriteCreateRequest) -> FavoriteResponse:
        self._require_database()
        with SessionLocal() as db:
            self._find_saved_project(db, request_data.project_id)

            existing_favorite = db.scalars(
                select(Favorite).where(
                    Favorite.user_id == request_data.user_id,
                    Favorite.project_id == request_data.project_id,
                )
            ).first()
            if existing_favorite:
                return self._to_favorite_response(existing_favorite)

            favorite = Favorite(**request_data.model_dump())
            db.add(favorite)
            db.commit()
            db.refresh(favorite)
            return self._to_favorite_response(favorite)

    def list_favorites(self, user_id: int | None = None) -> list[FavoriteResponse]:
        self._require_database()
        with SessionLocal() as db:
            statement = select(Favorite).order_by(Favorite.id)
            if user_id is not None:
                statement = statement.where(Favorite.user_id == user_id)
            favorites = db.scalars(statement).all()
            return [self._to_favorite_response(favorite) for favorite in favorites]

    def delete_favorite(self, favorite_id: int) -> MessageResponse:
        self._require_database()
        with SessionLocal() as db:
            favorite = db.get(Favorite, favorite_id)
            if favorite is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Favorite with id {favorite_id} not found.",
                )
            db.delete(favorite)
            db.commit()
            return MessageResponse(message="Favorite deleted successfully.")

    def _find_user(self, db, user_id: int) -> User:
        user = db.get(User, user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {user_id} not found.",
            )
        return user

    def _find_saved_project(self, db, project_id: int) -> SavedProject:
        project = db.get(SavedProject, project_id)
        if project is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with id {project_id} not found.",
            )
        return project

    def _to_user_response(self, user: User) -> UserResponse:
        return UserResponse(
            id=user.id,
            full_name=user.full_name,
            email=user.email,
            phone=user.phone,
            department=user.department,
            avatar_style=user.avatar_style,
            created_at=user.created_at,
        )

    def _to_favorite_response(self, favorite: Favorite) -> FavoriteResponse:
        return FavoriteResponse(
            id=favorite.id,
            user_id=favorite.user_id,
            project_id=favorite.project_id,
            created_at=favorite.created_at,
        )

    def _require_database(self) -> None:
        if not settings.enable_database:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database persistence is disabled.",
            )


user_service = UserService()
