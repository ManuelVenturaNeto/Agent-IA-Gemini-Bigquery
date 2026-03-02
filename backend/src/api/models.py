from typing import Optional
from pydantic import AliasChoices
from pydantic import BaseModel
from pydantic import EmailStr
from pydantic import Field
from pydantic import model_validator


SUPPORTED_RESPONSE_TYPES = ("TEXT", "SQL", "GRAPH")
RESPONSE_TYPE_ALIASES = {
    "GRAPHIC": "GRAPH",
}


def normalize_response_types(
    response_types: list[str] | None,
    response_type: str | None = None,
) -> list[str]:
    """Normalize response type selections into a canonical ordered list."""
    raw_values = list(response_types or [])
    if not raw_values and response_type:
        raw_values = [response_type]

    if not raw_values:
        raw_values = ["TEXT", "SQL"]

    normalized_values: list[str] = []
    seen_values: set[str] = set()

    for raw_value in raw_values:
        candidate = RESPONSE_TYPE_ALIASES.get(
            str(raw_value).strip().upper(),
            str(raw_value).strip().upper(),
        )
        if candidate not in SUPPORTED_RESPONSE_TYPES:
            raise ValueError(
                "response_types must contain only TEXT, SQL, or GRAPH."
            )
        if candidate in seen_values:
            continue

        normalized_values.append(candidate)
        seen_values.add(candidate)

    return normalized_values


class ModelRequest(BaseModel):
    email: EmailStr = Field(
        description="Authenticated user email. The backend currently validates the bearer token and uses that identity.",
        examples=["user@example.com"],
    )
    question: str = Field(
        description="Natural-language question that will be sent into the multi-agent pipeline.",
        examples=["How much did my travel expenses cost this month?"],
        min_length=1,
        max_length=4000,
    )
    chat_id: str = Field(
        description="Frontend-generated chat identifier used to group question history.",
        examples=["chat_demo_001"],
        min_length=1,
        max_length=64,
        pattern=r"^[A-Za-z0-9_-]+$",
    )
    question_id: str = Field(
        description="Frontend-generated unique question identifier for the current request.",
        examples=["question_demo_001"],
        min_length=1,
        max_length=64,
        pattern=r"^[A-Za-z0-9_-]+$",
    )
    response_types: list[str] = Field(
        default_factory=list,
        description=(
            "Requested response modes. Supported values are TEXT, SQL, and GRAPH."
        ),
        examples=[["TEXT", "SQL"]],
    )
    response_type: Optional[str] = Field(
        default=None,
        description="Deprecated single response mode alias.",
        examples=["TEXT"],
    )
    question_context: Optional[str] = Field(
        default=None,
        description="Optional context hint. Supported values are TRAVEL, EXPENSE, COMMERCIAL, and SERVICE.",
        examples=["TRAVEL"],
    )

    @model_validator(mode="after")
    def _normalize_response_types(self) -> "ModelRequest":
        """Normalize additive response modes and preserve the legacy alias."""
        self.response_types = normalize_response_types(
            response_types=self.response_types,
            response_type=self.response_type,
        )
        if self.response_type:
            self.response_type = normalize_response_types(
                response_types=[self.response_type],
            )[0]
        return self


class GraphRequest(BaseModel):
    chat_id: str = Field(
        description="Frontend-generated chat identifier used to group question history.",
        examples=["chat_demo_001"],
        min_length=1,
        max_length=64,
        pattern=r"^[A-Za-z0-9_-]+$",
    )
    question_id: str = Field(
        description="Frontend-generated unique question identifier for the current request.",
        examples=["question_demo_001"],
        min_length=1,
        max_length=64,
        pattern=r"^[A-Za-z0-9_-]+$",
    )
    graph_pattern_id: str = Field(
        description="Identifier of the graph pattern selected by the user.",
        examples=["bar_vertical"],
        min_length=1,
        max_length=64,
        pattern=r"^[A-Za-z0-9_-]+$",
    )


class LoginRequest(BaseModel):
    email: EmailStr = Field(
        description="Email used by the login endpoint.",
        examples=["user@example.com"],
        validation_alias=AliasChoices("email", "username"),
    )
    password: str = Field(
        description="Password used by the login endpoint.",
        examples=["demo_password"],
        min_length=1,
        max_length=256,
    )
