"""
ASCII Lab FastAPI application.
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import settings
from .api.routes_health import router as health_router
from .api.routes_image import router as image_router
from .api.routes_video import router as video_router


BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events.
    """

    settings.UPLOAD_DIR.mkdir(
        parents=True,
        exist_ok=True,
    ) if hasattr(
        settings.UPLOAD_DIR,
        "mkdir",
    ) else None

    settings.OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    ) if hasattr(
        settings.OUTPUT_DIR,
        "mkdir",
    ) else None

    yield


app = FastAPI(
    title="ASCII Lab",
    description=(
        "Python-based interactive "
        "ASCII rendering platform"
    ),
    version="1.0.0",
    lifespan=lifespan,
)


# ============================================================
# CORS
# ============================================================

origins = (
    settings.CORS_ORIGINS.split(",")
    if settings.CORS_ORIGINS != "*"
    else ["*"]
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=(
        settings.CORS_ORIGINS != "*"
    ),
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# API
# ============================================================

app.include_router(
    health_router,
    prefix="/api",
)

app.include_router(
    image_router,
    prefix="/api",
)

app.include_router(
    video_router,
    prefix="/api",
)


# ============================================================
# FRONTEND
# ============================================================

if FRONTEND_DIR.is_dir():

    app.mount(
        "/",
        StaticFiles(
            directory=str(
                FRONTEND_DIR
            ),
            html=True,
        ),
        name="frontend",
    )