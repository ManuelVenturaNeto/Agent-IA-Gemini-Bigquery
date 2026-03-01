from pydantic import BaseModel, EmailStr, Field


class ModelRequest(BaseModel):
    email: EmailStr = Field(
        description="Authenticated user email. The backend currently validates the bearer token and uses that identity.",
        examples=["manuueelneto@gmail.com"],
    )
    question: str = Field(
        description="Natural-language question that will be sent into the multi-agent pipeline.",
        examples=["How much did my travel expenses cost this month?"],
    )
    chat_id: str = Field(
        description="Frontend-generated chat identifier used to group question history.",
        examples=["a5b7b8f0de8342f2aaf87fd90c1fe123"],
    )
    question_id: str = Field(
        description="Frontend-generated unique question identifier for the current request.",
        examples=["e31cdb2d8a6142559ac4fe2e7c4a0ab1"],
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
        examples=["manuel"],
    )
    password: str = Field(
        description="Password used by the login endpoint.",
        examples=["123"],
    )
