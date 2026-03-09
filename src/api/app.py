from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from src.main.main import OrchestrateAgent
import logging

app = FastAPI(title="Data Agent API")
logger = logging.getLogger(__name__)

class AgentRequest(BaseModel):
    email: EmailStr
    question: str

@app.post("/v1/ask")
async def ask_agent(request: AgentRequest):
    logger.info(f"API Request received from {request.email}")
    try:
        orchestrator = OrchestrateAgent()
        result = orchestrator.run_agent(test_query=request.question, test_user=request.email)
        return {"response": result}

    except Exception as exp:
        logger.error(f"API Error: {exp}")
        raise HTTPException(status_code=500, detail="Internal server error in the agent pipeline.")