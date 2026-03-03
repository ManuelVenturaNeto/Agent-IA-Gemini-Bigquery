from typing import Any
from typing import Dict
from typing import Optional
from fastapi import APIRouter
from fastapi import Header
from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from src.agents.graph_agent import GraphAgent
from src.api.auth import validate_token
from src.api.config import api_audit
from src.api.config import chat_store_manager
from src.api.config import storage_manager
from src.api.models import GraphRequest
from src.api.models import ModelRequest
from src.main.main import OrchestrateAgent


router = APIRouter(tags=["Agent"])
graph_agent = GraphAgent(storage_manager)


class AgentRouteHandler:
    """Handles the API endpoint that runs the full agent pipeline."""

    async def ask_agent(
        self,
        request: ModelRequest,
        authorization: Optional[str] = Header(default=None),
    ) -> Dict[str, Any]:
        """Run the orchestrator and return the API response payload."""
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
                input_response_types=request.response_types,
            )

            result_payload = jsonable_encoder(result if isinstance(result, dict) else {})

            if result_payload.get("status") == "error":
                error_message = str(
                    result_payload.get("message") or "Invalid request."
                )
                chat_store_manager.upsert_mock_message(
                    request.chat_id,
                    request.question_id,
                    request.question,
                    response=error_message,
                    user_email=user_email,
                )
                raise HTTPException(
                    status_code=400,
                    detail=error_message,
                )

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
                graph_path=str(response_payload.get("graph_path") or ""),
                selected_graph_pattern=str(
                    response_payload.get("selected_graph_pattern") or ""
                ),
                response_types=list(response_payload.get("response_types") or []),
                graph_suggestions=list(
                    response_payload.get("graph_suggestions") or []
                ),
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
                "user": user_email,
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
            raise HTTPException(
                status_code=500,
                detail="Internal server error in the agent pipeline.",
            )

    async def generate_graph(
        self,
        request: GraphRequest,
        authorization: Optional[str] = Header(default=None),
    ) -> Dict[str, Any]:
        """Render a graph for previously persisted query data."""
        chat_id = request.chat_id
        question_id = request.question_id
        user_email = "SYSTEM"

        try:
            api_audit.log_info(
                "Graph endpoint received request.",
                chat_id=chat_id,
                question_id=question_id,
            )

            authenticated_user = validate_token(authorization)
            user_email = str(authenticated_user["email"])

            response_data = chat_store_manager.load_message_data(
                request.chat_id,
                request.question_id,
                user_email=user_email,
            )
            if response_data is None:
                raise HTTPException(
                    status_code=400,
                    detail="Saved response data was not found for this message.",
                )

            graph_suggestions = graph_agent.suggest_graphs(response_data)
            selected_graph = next(
                (
                    suggestion
                    for suggestion in graph_suggestions
                    if suggestion["id"] == request.graph_pattern_id
                ),
                None,
            )
            if selected_graph is None:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid graph pattern for the saved data.",
                )

            graph_path = graph_agent.render_graph(
                response_data=response_data,
                graph_pattern=selected_graph,
                user_email=user_email,
                chat_id=request.chat_id,
                question_id=request.question_id,
            )

            chat_store_manager.update_message_metadata(
                request.chat_id,
                request.question_id,
                graph_path=graph_path,
                selected_graph_pattern=request.graph_pattern_id,
                graph_suggestions=graph_suggestions,
                user_email=user_email,
            )

            api_audit.log_info(
                "Graph endpoint completed successfully.",
                user_email=user_email,
                chat_id=chat_id,
                question_id=question_id,
            )
            return {
                "status": "success",
                "status_code": 200,
                "chat_id": request.chat_id,
                "question_id": request.question_id,
                "graph_path": graph_path,
                "selected_graph_pattern": request.graph_pattern_id,
                "graph_suggestions": graph_suggestions,
            }
        except HTTPException as exp:
            api_audit.log_warning(
                f"Graph HTTP exception raised: {exp.detail}",
                user_email=user_email,
                chat_id=chat_id,
                question_id=question_id,
            )
            raise
        except Exception as exp:
            api_audit.log_error(
                f"Graph API error: {exp}",
                user_email=user_email,
                chat_id=chat_id,
                question_id=question_id,
            )
            raise HTTPException(
                status_code=500,
                detail="Internal server error while generating the graph.",
            )


agent_route_handler = AgentRouteHandler()
ask_agent = agent_route_handler.ask_agent
generate_graph = agent_route_handler.generate_graph

router.add_api_route(
    "/v1/ask",
    endpoint=ask_agent,
    methods=["POST"],
    summary="Run The Agent Pipeline",
    description=(
        "Runs the full backend pipeline: validates the bearer token, stores the incoming "
        "question, routes the question context, generates SQL, executes the BigQuery query, "
        "stores any returned data, and returns the formatted response payload."
    ),
    response_description=(
        "Agent execution result, including SQL, structured data, and natural-language response."
    ),
    responses={
        400: {
            "description": "The request was rejected because it was invalid or not business-related.",
        },
        401: {
            "description": "Missing, malformed, or invalid authorization token.",
        },
        500: {
            "description": "Unhandled backend failure while processing the pipeline.",
        },
    },
)

router.add_api_route(
    "/v1/graph",
    endpoint=generate_graph,
    methods=["POST"],
    summary="Generate Graph",
    description=(
        "Loads previously saved structured data for a message, validates the selected "
        "graph pattern, renders a PNG graph, and stores it in backend storage."
    ),
    response_description="Graph rendering result for a previously processed message.",
    responses={
        400: {
            "description": "The saved data was missing or the graph pattern was invalid.",
        },
        401: {
            "description": "Missing, malformed, or invalid authorization token.",
        },
        500: {
            "description": "Unhandled backend failure while generating the graph.",
        },
    },
)
