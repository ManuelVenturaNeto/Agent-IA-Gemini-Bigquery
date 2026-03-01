from fastapi import APIRouter, Cookie, HTTPException
from fastapi.responses import FileResponse, RedirectResponse, Response

from src.api.auth import validate_token
from src.api.config import api_audit, chat_store_manager, frontend_dir, login_page


router = APIRouter()


@router.get("/", response_class=FileResponse)
async def serve_frontend(
    session_token: str | None = Cookie(default=None, alias="ia_agent_auth_token"),
) -> Response:
    if not session_token:
        api_audit.log_debug("Missing session cookie. Redirecting to login.")
        return RedirectResponse(url="/login", status_code=303)

    try:
        validate_token(f"Bearer {session_token}")
    except HTTPException:
        api_audit.log_warning("Invalid session cookie. Redirecting to login.")
        return RedirectResponse(url="/login", status_code=303)

    api_audit.log_debug("Serving frontend shell.")
    return FileResponse(frontend_dir / "index.html")


@router.get("/login", response_class=FileResponse)
async def serve_login(
    session_token: str | None = Cookie(default=None, alias="ia_agent_auth_token"),
) -> Response:
    if session_token:
        try:
            validate_token(f"Bearer {session_token}")
            api_audit.log_debug("Valid session cookie found on login route. Redirecting to app.")
            return RedirectResponse(url="/", status_code=303)
        except HTTPException:
            api_audit.log_warning("Invalid session cookie found on login route. Serving login shell.")

    api_audit.log_debug("Serving login shell.")
    return FileResponse(login_page)


@router.get("/chat_mensages.json", response_class=FileResponse)
async def serve_chat_messages() -> FileResponse:
    store = chat_store_manager.load_chat_store()
    api_audit.log_debug(
        f"Serving chat history. Messages: {len(store['mensages'])}.",
        chat_id=str(store["chat_id"]),
    )
    return FileResponse(chat_store_manager.chat_messages_path, media_type="application/json")
