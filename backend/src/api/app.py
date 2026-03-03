from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from src.api.config import assets_dir
from src.api.routes.agent import router as agent_router
from src.api.routes.auth import router as auth_router
from src.api.routes.pages import router as pages_router


API_DESCRIPTION = """
Backend API for the Analytical Agent project.

Main responsibilities:
- authenticate the user and validate the in-memory bearer token
- orchestrate the multi-agent pipeline that classifies the request, generates SQL, runs BigQuery, and formats the answer
- serve the frontend shell and static assets used by the web interface

Interactive documentation:
- Swagger UI: `/docs`
- ReDoc: `/redoc`
""".strip()

API_TAGS_METADATA = [
    {
        "name": "Authentication",
        "description": "Login and session validation endpoints.",
    },
    {
        "name": "Agent",
        "description": "Question processing and multi-agent orchestration endpoints.",
    },
]


app = FastAPI(
    title="Analytical Agent Backend API",
    summary="FastAPI backend for the Analytical Agent project.",
    description=API_DESCRIPTION,
    version="1.0.0",
    openapi_tags=API_TAGS_METADATA,
)

app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
app.include_router(pages_router)
app.include_router(auth_router)
app.include_router(agent_router)
