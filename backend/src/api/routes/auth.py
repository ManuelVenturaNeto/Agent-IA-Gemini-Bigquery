from typing import Any
from typing import Dict
from typing import Optional
from fastapi import APIRouter
from fastapi import Header
from src.api.auth import login_user
from src.api.auth import validate_token
from src.api.config import api_audit
from src.api.models import LoginRequest


router = APIRouter(tags=["Authentication"])


class AuthRouteHandler:
    """Handles the authentication HTTP endpoints."""

    async def login(self, request: LoginRequest) -> Dict[str, str]:
        """Return a bearer token payload for valid credentials."""
        payload = login_user(request.username, request.password)
        api_audit.log_info("Login endpoint completed.", user_email=payload["email"])
        return payload

    async def session_status(
        self,
        authorization: Optional[str] = Header(default=None),
    ) -> Dict[str, Any]:
        """Validate the bearer token and return the authenticated user."""
        authenticated_user = validate_token(authorization)
        api_audit.log_info(
            "Session endpoint validated user.",
            user_email=authenticated_user["email"],
        )
        return {
            "status": "success",
            "status_code": 200,
            "username": authenticated_user["username"],
            "email": authenticated_user["email"],
        }


auth_route_handler = AuthRouteHandler()
login = auth_route_handler.login
session_status = auth_route_handler.session_status

router.add_api_route(
    "/v1/login",
    endpoint=login,
    methods=["POST"],
    summary="Authenticate User",
    description=(
        "Validates the provided username and password and returns a bearer token "
        "used by the frontend."
    ),
    response_description=(
        "Authentication payload containing the bearer token and user identity."
    ),
    responses={
        401: {
            "description": "Invalid credentials.",
        },
    },
)

router.add_api_route(
    "/v1/session",
    endpoint=session_status,
    methods=["GET"],
    summary="Validate Session",
    description=(
        "Validates the bearer token received in the Authorization header and "
        "returns the authenticated user."
    ),
    response_description="Session validation result for the current bearer token.",
    responses={
        401: {
            "description": "Missing, malformed, or invalid authorization token.",
        },
    },
)
