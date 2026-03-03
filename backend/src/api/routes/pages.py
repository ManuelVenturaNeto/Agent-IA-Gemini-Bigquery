from typing import Any
from typing import Dict
from typing import Optional
from fastapi import APIRouter
from fastapi import Cookie
from fastapi import Header
from fastapi import HTTPException
from fastapi.responses import FileResponse
from fastapi.responses import JSONResponse
from fastapi.responses import RedirectResponse
from fastapi.responses import Response
from src.api.auth import validate_token
from src.api.config import api_audit
from src.api.config import chat_store_manager
from src.api.config import frontend_dir
from src.api.config import login_page
from src.api.config import pipeline_log_path
from src.api.config import storage_manager


router = APIRouter()


class PagesRouteHandler:
    """Handles the frontend page and storage proxy endpoints."""

    def __init__(self) -> None:
        """Prepare the list of log fragments hidden from the runtime panel."""
        self._hidden_runtime_log_fragments = (
            "/v1/runtime-logs",
            "Serving runtime logs panel.",
        )

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

    async def serve_runtime_logs(
        self,
        authorization: Optional[str] = Header(default=None),
        line_count: int = 60,
    ) -> Dict[str, Any]:
        """Return the latest application logs for privileged authenticated users."""
        authenticated_user = validate_token(
            authorization,
            should_log_success=False,
        )
        can_view_runtime_logs = bool(
            authenticated_user.get("can_view_runtime_logs")
        )

        if not can_view_runtime_logs:
            return {
                "can_view_runtime_logs": False,
                "logs": "",
            }

        logs = ""
        if pipeline_log_path.exists():
            normalized_line_count = 60
            try:
                normalized_line_count = int(line_count)
            except (TypeError, ValueError):
                normalized_line_count = 60

            normalized_line_count = max(20, min(normalized_line_count, 1000))
            lines = pipeline_log_path.read_text(
                encoding="utf-8",
                errors="replace",
            ).splitlines()
            visible_lines = self._filter_runtime_panel_lines(lines)
            logs = "\n".join(visible_lines[-normalized_line_count:])

        return {
            "can_view_runtime_logs": True,
            "logs": logs,
        }

    async def serve_stored_data(
        self,
        chat_id: str,
        message_id: str,
        session_token: Optional[str] = Cookie(default=None, alias="ia_agent_auth_token"),
    ) -> Response:
        """Proxy stored JSON data from cloud storage for the authenticated user."""
        authenticated_user = self._validate_session_cookie(session_token)
        response_data = storage_manager.load_json_data(
            user_email=str(authenticated_user["email"]),
            chat_id=chat_id,
            message_id=message_id,
        )
        if response_data is None:
            raise HTTPException(
                status_code=404,
                detail="Saved response data was not found for this message.",
            )

        return JSONResponse(content=response_data)

    async def serve_stored_graph(
        self,
        chat_id: str,
        message_id: str,
        session_token: Optional[str] = Cookie(default=None, alias="ia_agent_auth_token"),
    ) -> Response:
        """Proxy a stored graph image from cloud storage for the authenticated user."""
        authenticated_user = self._validate_session_cookie(session_token)
        graph_bytes = storage_manager.load_graph_image(
            user_email=str(authenticated_user["email"]),
            chat_id=chat_id,
            message_id=message_id,
        )
        if graph_bytes is None:
            raise HTTPException(
                status_code=404,
                detail="Saved graph was not found for this message.",
            )

        return Response(content=graph_bytes, media_type="image/png")

    def _filter_runtime_panel_lines(self, lines: list[str]) -> list[str]:
        """Remove runtime-panel self-referential lines from the visible log stream."""
        visible_lines = []

        for line in lines:
            if self._should_hide_runtime_line(line):
                continue

            visible_lines.append(line)

        return visible_lines

    def _should_hide_runtime_line(self, line: str) -> bool:
        """Return True when a log line should be hidden from the runtime panel."""
        for fragment in self._hidden_runtime_log_fragments:
            if fragment in line:
                return True

        return False

    def _validate_session_cookie(
        self,
        session_token: Optional[str],
    ) -> Dict[str, Any]:
        """Validate the app session cookie and return the authenticated user."""
        if not session_token:
            raise HTTPException(
                status_code=401,
                detail="Missing session cookie.",
            )

        return validate_token(f"Bearer {session_token}")


pages_route_handler = PagesRouteHandler()
serve_frontend = pages_route_handler.serve_frontend
serve_login = pages_route_handler.serve_login
serve_chat_messages = pages_route_handler.serve_chat_messages
serve_runtime_logs = pages_route_handler.serve_runtime_logs
serve_stored_data = pages_route_handler.serve_stored_data
serve_stored_graph = pages_route_handler.serve_stored_graph

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

router.add_api_route(
    "/v1/runtime-logs",
    endpoint=serve_runtime_logs,
    methods=["GET"],
    include_in_schema=False,
)

router.add_api_route(
    "/v1/storage/data/{chat_id}/{message_id}",
    endpoint=serve_stored_data,
    methods=["GET"],
    include_in_schema=False,
)

router.add_api_route(
    "/v1/storage/graph/{chat_id}/{message_id}",
    endpoint=serve_stored_graph,
    methods=["GET"],
    include_in_schema=False,
)
