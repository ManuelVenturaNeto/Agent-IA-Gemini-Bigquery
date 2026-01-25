from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from src.main.main import OrchestrateAgent
import logging

app = FastAPI(title="Data Agent API")
logger = logging.getLogger(__name__)

class ModelRequest(BaseModel):
    email: EmailStr
    question: str

@app.post("/v1/ask")
async def ask_agent(request: ModelRequest):
    try:
        orchestrator = OrchestrateAgent()
        result = orchestrator.run_agent(input_question=request.question, input_user=request.email)
        
        logger.info(f"API Request received from {request.email}")
        logger.debug(f"Question: {request.question}")

        return {"response": result}

    except Exception as exp:
        logger.error(f"API Error: {exp}")
        raise HTTPException(status_code=500, detail="Internal server error in the agent pipeline.")