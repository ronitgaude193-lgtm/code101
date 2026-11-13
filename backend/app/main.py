from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.database.session import init_database, close_pool
from app.execution.judge0_client import judge0_client
from app.ai_mentor.service import ai_mentor_service

from app.auth.router import router as auth_router
from app.challenges.router import router as challenges_router
from app.execution.router import router as execution_router
from app.ai_mentor.router import router as ai_router
from app.analytics.router import router as analytics_router
from app.achievements.router import router as achievements_router
from app.academy.router import router as academy_router
from app.roadmap.router import router as roadmap_router
from app.mistake_memory.router import router as memory_router
from app.assistance.router import router as assist_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables and seed foundational challenges/achievements
    init_database()
    yield
    close_pool()

app = FastAPI(
    title="AI Coding Mentor API",
    description="Intelligent Adaptive Programming Learning Platform Backend",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In development allow all for seamless connectivity
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register sub-routers
app.include_router(auth_router)
app.include_router(challenges_router)
app.include_router(execution_router)
app.include_router(ai_router)
app.include_router(analytics_router)
app.include_router(achievements_router)
app.include_router(academy_router)
app.include_router(roadmap_router)
app.include_router(memory_router)
app.include_router(assist_router)

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "app": "AI Coding Mentor API",
        "version": "1.0.0",
        "environment": settings.APP_ENV,
        "execution_provider": "Judge0 API" if judge0_client.is_configured() else "Isolated Local Sandbox (Judge0 credentials unconfigured)",
        "ai_provider": settings.AI_PROVIDER if ai_mentor_service.is_configured() else "Offline Pedagogical Rule Engine (AI credentials unconfigured)"
    }

# Mount frontend production build if present for unified full-stack serving
import os
from starlette.staticfiles import StaticFiles
from starlette.responses import FileResponse

dist_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist"))
if os.path.exists(dist_dir):
    app.mount("/assets", StaticFiles(directory=os.path.join(dist_dir, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = os.path.join(dist_dir, full_path)
        if full_path and os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(dist_dir, "index.html"))

