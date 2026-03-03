from secrets import token_urlsafe
from typing import Dict
from typing import Optional
from fastapi import HTTPException
from fastapi import status
from src.infra.config import settings
from src.infra.logging_utils import LoggedComponent


_active_tokens: Dict[str, Dict[str, object]] = {}


class AuthService(LoggedComponent):
    """Authenticates users and validates in-memory bearer tokens."""

    def __init__(self) -> None:
        """Load login settings and initialize the auth logger."""
        super().__init__()
        self._login_password = settings.app_login_password
        self._privileged_log_emails = settings.privileged_log_viewer_emails

    def login_user(self, email: str, password: str) -> Dict[str, object]:
        """Authenticate an email and return the bearer token payload."""
        normalized_email = email.strip().lower()
        self.log_info(f"Login attempt for email: {normalized_email}")

        if password != self._login_password:
            self.log_warning(f"Invalid login attempt for email: {normalized_email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
            )

        can_view_runtime_logs = normalized_email in self._privileged_log_emails
        token = token_urlsafe(24)
        _active_tokens[token] = {
            "email": normalized_email,
            "can_view_runtime_logs": can_view_runtime_logs,
        }

        self.log_info("Login successful.", user_email=normalized_email)
        return {
            "access_token": token,
            "token_type": "bearer",
            "email": normalized_email,
            "can_view_runtime_logs": can_view_runtime_logs,
        }

    def validate_token(
        self,
        authorization: Optional[str],
        should_log_success: bool = True,
    ) -> Dict[str, object]:
        """Validate the Authorization header and return the stored user payload."""
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

        if should_log_success:
            self.log_info("Token validated.", user_email=str(user["email"]))
        return user


auth_service = AuthService()
login_user = auth_service.login_user
validate_token = auth_service.validate_token
