from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from src.api.config import assets_dir, chat_store_manager
from src.api.routes.agent import router as agent_router
from src.api.routes.auth import router as auth_router
from src.api.routes.pages import router as pages_router


app = FastAPI(title="Data Agent API")

app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
app.mount("/storage", StaticFiles(directory=chat_store_manager.storage_dir), name="storage")
app.include_router(pages_router)
app.include_router(auth_router)
app.include_router(agent_router)
