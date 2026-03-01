from typing import Optional
from fastapi import APIRouter
from fastapi import Cookie
from fastapi import HTTPException
from fastapi.responses import FileResponse
from fastapi.responses import RedirectResponse
from fastapi.responses import Response
from src.api.auth import validate_token
from src.api.config import api_audit
from src.api.config import chat_store_manager
from src.api.config import frontend_dir
from src.api.config import login_page


router = APIRouter()


class PagesRouteHandler:
    """Handles the frontend page and local file endpoints."""

    async def serve_frontend(
        self,
        session_token: Optional[str] = Cookie(default=None, alias="ia_agent_auth_token"),
    ) -> Response:
        """Serve the frontend shell for valid sessions or redirect to login."""
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

    async def serve_login(
        self,
        session_token: Optional[str] = Cookie(default=None, alias="ia_agent_auth_token"),
    ) -> Response:
        """Serve the login page or redirect authenticated users to the app."""
        if session_token:
            try:
                validate_token(f"Bearer {session_token}")
                api_audit.log_debug(
                    "Valid session cookie found on login route. Redirecting to app."
                )
                return RedirectResponse(url="/", status_code=303)
            except HTTPException:
                api_audit.log_warning(
                    "Invalid session cookie found on login route. Serving login shell."
                )

        api_audit.log_debug("Serving login shell.")
        return FileResponse(login_page)

    async def serve_chat_messages(self) -> FileResponse:
        """Serve the persisted local chat history JSON file."""
        store = chat_store_manager.load_chat_store()
        api_audit.log_debug(
            f"Serving chat history. Messages: {len(store['mensages'])}.",
            chat_id=str(store["chat_id"]),
        )
        return FileResponse(
            chat_store_manager.chat_messages_path,
            media_type="application/json",
        )


pages_route_handler = PagesRouteHandler()
serve_frontend = pages_route_handler.serve_frontend
serve_login = pages_route_handler.serve_login
serve_chat_messages = pages_route_handler.serve_chat_messages

router.add_api_route(
    "/",
    endpoint=serve_frontend,
    methods=["GET"],
    response_class=FileResponse,
    include_in_schema=False,
)

router.add_api_route(
    "/login",
    endpoint=serve_login,
    methods=["GET"],
    response_class=FileResponse,
    include_in_schema=False,
)

router.add_api_route(
    "/chat_messages.json",
    endpoint=serve_chat_messages,
    methods=["GET"],
    response_class=FileResponse,
    include_in_schema=False,
)
