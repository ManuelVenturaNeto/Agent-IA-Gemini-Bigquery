from pydantic import BaseModel, EmailStr, Field


class ModelRequest(BaseModel):
    email: EmailStr = Field(
        description="Authenticated user email. The backend currently validates the bearer token and uses that identity.",
        examples=["user@example.com"],
    )
    question: str = Field(
        description="Natural-language question that will be sent into the multi-agent pipeline.",
        examples=["How much did my travel expenses cost this month?"],
    )
    chat_id: str = Field(
        description="Frontend-generated chat identifier used to group question history.",
        examples=["chat_demo_001"],
    )
    question_id: str = Field(
        description="Frontend-generated unique question identifier for the current request.",
        examples=["question_demo_001"],
    )
    response_type: str | None = Field(
        default=None,
        description="Requested response mode. Supported values in the current UI are TEXT, SQL, and GRAPHIC.",
        examples=["TEXT"],
    )
    question_context: str | None = Field(
        default=None,
        description="Optional context hint. Supported values are TRAVEL, EXPENSE, COMMERCIAL, and SERVICE.",
        examples=["TRAVEL"],
    )


class LoginRequest(BaseModel):
    username: str = Field(
        description="Username used by the login endpoint.",
        examples=["demo_user"],
    )
    password: str = Field(
        description="Password used by the login endpoint.",
        examples=["demo_password"],
    )
