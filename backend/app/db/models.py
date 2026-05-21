from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    phone = Column(String(50), nullable=True)
    department = Column(String(255), nullable=True)
    password = Column(String(255), nullable=False)  # TODO: replace plain password with password hashing in production.
    avatar_style = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    favorites = relationship("Favorite", back_populates="user", cascade="all, delete-orphan")
    chat_sessions = relationship(
        "ChatSession", back_populates="user", cascade="all, delete-orphan"
    )


class SavedProject(Base):
    __tablename__ = "saved_projects"

    id = Column(Integer, primary_key=True, index=True)
    owner_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    title = Column(String(255), nullable=False, index=True)
    category = Column(String(100), nullable=False, index=True)
    difficulty = Column(String(50), nullable=False, index=True)
    duration_months = Column(Integer, nullable=False)
    tech_stack = Column(JSON, nullable=False, default=list)
    description = Column(Text, nullable=False)
    problem = Column(Text, nullable=False)
    solution = Column(Text, nullable=False)
    features = Column(JSON, nullable=False, default=list)
    evaluation_metrics = Column(JSON, nullable=False, default=list)
    paper_link = Column(String(500), nullable=True)
    github_link = Column(String(500), nullable=True)
    feasibility_score = Column(Integer, nullable=False, default=0)
    scope = Column(Text, nullable=True)
    architecture_summary = Column(Text, nullable=True)
    weekly_milestones = Column(JSON, nullable=False, default=list)
    risks = Column(JSON, nullable=False, default=list)
    source_status = Column(String(50), nullable=True)
    source_titles = Column(JSON, nullable=False, default=list)
    source_quality_score = Column(Integer, nullable=True)
    paper_score = Column(Integer, nullable=True)
    repository_score = Column(Integer, nullable=True)
    raw_project = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    favorites = relationship(
        "Favorite", back_populates="project", cascade="all, delete-orphan"
    )
    chat_sessions = relationship("ChatSession", back_populates="project")


class Favorite(Base):
    __tablename__ = "favorites"
    __table_args__ = (
        UniqueConstraint("user_id", "project_id", name="uq_favorites_user_project"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    project_id = Column(Integer, ForeignKey("saved_projects.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="favorites")
    project = relationship("SavedProject", back_populates="favorites")


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    project_id = Column(Integer, ForeignKey("saved_projects.id"), nullable=True)
    title = Column(String(255), nullable=False)
    project_snapshot = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="chat_sessions")
    project = relationship("SavedProject", back_populates="chat_sessions")
    messages = relationship(
        "ChatMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at",
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False, index=True)
    role = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    session = relationship("ChatSession", back_populates="messages")
