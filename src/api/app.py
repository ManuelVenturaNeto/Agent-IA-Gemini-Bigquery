import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from src.main.main import OrchestrateAgent


app = FastAPI(title="Data Agent API")
logger = logging.getLogger(__name__)

class ModelRequest(BaseModel):
    email: EmailStr
    question: str
    chat_id: str
    question_id: str
    response_type: str | None = None
    question_context: str | None = None


@app.post("/v1/ask")
async def ask_agent(request: ModelRequest) -> dict[str, object]:
    """
    API endpoint that runs the multi-agent pipeline.
    """
    try:
        orchestrator = OrchestrateAgent()

        result = orchestrator.run_agent(
            input_question=request.question,
            input_user=str(request.email),
            input_chat_id=request.chat_id,
            input_question_id=request.question_id,
            input_response_type=request.response_type,
            input_question_context=request.question_context,
        )

        logger.info(
            "[INFO] email: %s | question_id: %s | chat_id: %s | question: %s",
            request.email,
            request.question_id,
            request.chat_id,
            request.question,
        )

        return {
            "status": "success",
            "status_code": 200,
            "email": request.email,
            "chat_id": request.chat_id,
            "question_id": request.question_id,
            "question": request.question,
            "response": result,
        }

    except Exception as exp:
        logger.error("API Error: %s", exp)
        raise HTTPException(status_code=500, detail="Internal server error in the agent pipeline.")
