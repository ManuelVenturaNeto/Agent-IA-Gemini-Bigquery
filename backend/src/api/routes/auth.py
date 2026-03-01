from fastapi import APIRouter, Header

from src.api.auth import login_user, validate_token
from src.api.config import api_audit
from src.api.models import LoginRequest


router = APIRouter(tags=["Authentication"])


@router.post(
    "/v1/login",
    summary="Authenticate User",
    description="Validates the provided username and password and returns a bearer token used by the frontend.",
    response_description="Authentication payload containing the bearer token and user identity.",
    responses={
        401: {
            "description": "Invalid credentials.",
        },
    },
)
async def login(request: LoginRequest) -> dict[str, str]:
    payload = login_user(request.username, request.password)
    api_audit.log_info("Login endpoint completed.", user_email=payload["email"])
    return payload


@router.get(
    "/v1/session",
    summary="Validate Session",
    description="Validates the bearer token received in the Authorization header and returns the authenticated user.",
    response_description="Session validation result for the current bearer token.",
    responses={
        401: {
            "description": "Missing, malformed, or invalid authorization token.",
        },
    },
)
async def session_status(
    authorization: str | None = Header(default=None),
) -> dict[str, object]:
    authenticated_user = validate_token(authorization)
    api_audit.log_info("Session endpoint validated user.", user_email=authenticated_user["email"])
    return {
        "status": "success",
        "status_code": 200,
        "username": authenticated_user["username"],
        "email": authenticated_user["email"],
    }
