from pydantic import BaseModel, EmailStr


class ModelRequest(BaseModel):
    email: EmailStr
    question: str
    chat_id: str
    question_id: str
    response_type: str | None = None
    question_context: str | None = None


class LoginRequest(BaseModel):
    username: str
    password: str
