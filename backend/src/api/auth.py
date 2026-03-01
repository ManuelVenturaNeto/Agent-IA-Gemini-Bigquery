from secrets import token_urlsafe
from typing import Final

from fastapi import HTTPException, status

from src.infra.logging_utils import LoggedComponent


MOCK_USERNAME: Final[str] = "demo_user"
MOCK_PASSWORD: Final[str] = "demo_password"
MOCK_EMAIL: Final[str] = "user@example.com"

_active_tokens: dict[str, dict[str, str]] = {}


class AuthService(LoggedComponent):
    def __init__(self) -> None:
        super().__init__()

    def login_user(self, username: str, password: str) -> dict[str, str]:
        self.log_info(f"Login attempt for username: {username}")

        if username != MOCK_USERNAME or password != MOCK_PASSWORD:
            self.log_warning(f"Invalid login attempt for username: {username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password.",
            )

        token = token_urlsafe(24)
        _active_tokens[token] = {
            "username": username,
            "email": MOCK_EMAIL,
        }

        self.log_info("Login successful.", user_email=MOCK_EMAIL)
        return {
            "access_token": token,
            "token_type": "bearer",
            "username": username,
            "email": MOCK_EMAIL,
        }

    def validate_token(self, authorization: str | None) -> dict[str, str]:
        if not authorization:
            self.log_warning("Missing authorization header.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing authorization header.",
            )

        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not token:
            self.log_warning("Invalid authorization header.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header.",
            )

        user = _active_tokens.get(token)
        if not user:
            self.log_warning("Invalid or expired token.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token.",
            )

        self.log_info("Token validated.", user_email=user["email"])
        return user


auth_service = AuthService()


def login_user(username: str, password: str) -> dict[str, str]:
    return auth_service.login_user(username, password)


def validate_token(authorization: str | None) -> dict[str, str]:
    return auth_service.validate_token(authorization)
