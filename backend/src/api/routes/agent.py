from fastapi import APIRouter, Header, HTTPException
from fastapi.encoders import jsonable_encoder

from src.api.auth import validate_token
from src.api.config import api_audit, chat_store_manager
from src.api.models import ModelRequest
from src.main.main import OrchestrateAgent


router = APIRouter(tags=["Agent"])


@router.post(
    "/v1/ask",
    summary="Run The Agent Pipeline",
    description=(
        "Runs the full backend pipeline: validates the bearer token, stores the incoming question, "
        "routes the question context, generates SQL, executes the BigQuery query, stores any returned data, "
        "and returns the formatted response payload."
    ),
    response_description="Agent execution result, including SQL, structured data, and natural-language response.",
    responses={
        401: {
            "description": "Missing, malformed, or invalid authorization token.",
        },
        500: {
            "description": "Unhandled backend failure while processing the pipeline.",
        },
    },
)
async def ask_agent(
    request: ModelRequest,
    authorization: str | None = Header(default=None),
) -> dict[str, object]:
    """
    API endpoint that runs the multi-agent pipeline.
    """
    user_email = str(request.email)
    chat_id = request.chat_id
    question_id = request.question_id

    try:
        api_audit.log_info(
            "Ask endpoint received request.",
            user_email=user_email,
            chat_id=chat_id,
            question_id=question_id,
        )

        authenticated_user = validate_token(authorization)
        user_email = authenticated_user["email"]

        chat_store_manager.upsert_mock_message(
            request.chat_id,
            request.question_id,
            request.question,
            user_email=user_email,
        )

        orchestrator = OrchestrateAgent()
        result = orchestrator.run_agent(
            input_question=request.question,
            input_user=user_email,
            input_chat_id=request.chat_id,
            input_question_id=request.question_id,
            input_response_type=request.response_type,
            input_question_context=request.question_context,
        )

        result_payload = jsonable_encoder(result if isinstance(result, dict) else {})
        data_path = chat_store_manager.save_message_data(
            request.chat_id,
            request.question_id,
            result_payload.get("response_data"),
            user_email=user_email,
        )

        response_payload = dict(result_payload)
        response_payload["data_path"] = data_path

        chat_store_manager.upsert_mock_message(
            request.chat_id,
            request.question_id,
            request.question,
            response=str(response_payload.get("response_natural_language") or ""),
            query=str(response_payload.get("response_sql") or ""),
            data_path=data_path,
            user_email=user_email,
        )

        api_audit.log_info(
            "Ask endpoint completed successfully.",
            user_email=user_email,
            chat_id=chat_id,
            question_id=question_id,
        )
        return {
            "status": "success",
            "status_code": 200,
            "user": authenticated_user["username"],
            "email": user_email,
            "chat_id": request.chat_id,
            "question_id": request.question_id,
            "question": request.question,
            "response": response_payload,
        }

    except HTTPException as exp:
        api_audit.log_warning(
            f"HTTP exception raised: {exp.detail}",
            user_email=user_email,
            chat_id=chat_id,
            question_id=question_id,
        )
        raise
    except Exception as exp:
        api_audit.log_error(
            f"API error: {exp}",
            user_email=user_email,
            chat_id=chat_id,
            question_id=question_id,
        )
        raise HTTPException(status_code=500, detail="Internal server error in the agent pipeline.")
