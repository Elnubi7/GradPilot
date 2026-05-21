import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.database import create_tables
from app.routes.advisor_routes import router as advisor_router
from app.routes.chat_routes import router as chat_router
from app.routes.project_routes import router as project_router
from app.routes.source_routes import router as source_router
from app.routes.user_routes import router as user_router


logger = logging.getLogger(__name__)


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=settings.app_description,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(project_router, prefix="/projects", tags=["Projects"])
app.include_router(advisor_router, prefix="/advisor", tags=["Advisor"])
app.include_router(source_router, prefix="/sources", tags=["Sources"])
app.include_router(user_router)
app.include_router(chat_router, prefix="/chat", tags=["Chat"])


@app.on_event("startup")
def startup_event() -> None:
    if not settings.enable_database:
        return

    try:
        create_tables()
        logger.info("Database tables initialized successfully.")
    except Exception as exc:
        logger.error("Database initialization failed: %s", exc)


@app.get("/")
def read_root() -> dict[str, str]:
    return {
        "message": f"Welcome to {settings.app_name}",
        "docs": "/docs",
    }


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
