import os
import logging
from typing import Dict, Any
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.dependencies import get_container, get_llm_service, get_store
from backend.api import (
    profile, goal, graph, assessment,
    knowledge, gaps, recommendations,
    roadmap, tutor, feedback, dashboard, presets
)

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("xcl_pathfinder_api")

app = FastAPI(
    title="XCL PathFinder — Adaptive Career Copilot API",
    description="REST API backend for personalized career skill graph navigation, diagnostic assessment, topological roadmaps, and continuous AI tutoring.",
    version="2.0.0"
)

# CORS Configuration
allowed_origins_env = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000")
allowed_origins = [origin.strip() for origin in allowed_origins_env.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers under /api
app.include_router(profile.router, prefix="/api")
app.include_router(goal.router, prefix="/api")
app.include_router(graph.router, prefix="/api")
app.include_router(assessment.router, prefix="/api")
app.include_router(knowledge.router, prefix="/api")
app.include_router(gaps.router, prefix="/api")
app.include_router(recommendations.router, prefix="/api")
app.include_router(roadmap.router, prefix="/api")
app.include_router(tutor.router, prefix="/api")
app.include_router(feedback.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(presets.router, prefix="/api")

@app.get("/api/health", tags=["Health"])
def health_check() -> Dict[str, Any]:
    """Health check returning API status, Gemini model configuration, and store state."""
    llm = get_llm_service()
    store = get_store()
    return {
        "status": "healthy",
        "service": "XCL PathFinder FastAPI Backend",
        "version": "2.0.0",
        "gemini_model": llm.model_name,
        "gemini_configured": bool(llm.client),
        "authoritative_store": {
            "profile_loaded": bool(store.profile and store.profile.name),
            "goal_active": bool(store.goal_state and store.goal_state.active),
            "knowledge_states_count": len(store.knowledge_states),
            "active_roadmap_version": store.current_roadmap_version,
            "feedback_events_count": len(store.feedback_events)
        }
    }

@app.get("/", tags=["Root"])
def root():
    return {
        "message": "Welcome to XCL PathFinder Adaptive Career Copilot API",
        "documentation": "/docs",
        "health": "/api/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
