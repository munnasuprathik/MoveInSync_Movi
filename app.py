import json
import logging
import os
from typing import Any, List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool
from langchain_anthropic import ChatAnthropic
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import ToolException
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from pydantic import BaseModel

from backend.mcp import (
    ConsequenceWarning,
    VisionExtraction,
    VisionProcessingError,
    analyze_trip_removal_request,
    process_dashboard_image,
)
from database.repositories import DeploymentsRepository
from backend.routes import (
    deployments,
    drivers,
    paths,
    routes,
    stops,
    trips,
    vehicles,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Loading environment variables from .env")
load_dotenv()

PROJECT_REF = os.environ.get("SUPABASE_PROJECT_REF")
ACCESS_TOKEN = os.environ.get("SUPABASE_ACCESS_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
SYSTEM_USER_ID = int(os.environ.get("SYSTEM_USER_ID", "1"))

if not PROJECT_REF or not ACCESS_TOKEN:
    raise RuntimeError("SUPABASE_PROJECT_REF and SUPABASE_ACCESS_TOKEN must be set.")

SUPABASE_URL = (
    f"https://mcp.supabase.com/mcp?project_ref={PROJECT_REF}&features=database"
)
SUPABASE_HEADERS = {"Authorization": f"Bearer {ACCESS_TOKEN}"}


def initialize_claude_model(api_key: Optional[str]) -> Optional[ChatAnthropic]:
    if not api_key:
        logger.warning("ANTHROPIC API key not found; Claude model will not be available.")
        return None
    os.environ["ANTHROPIC_API_KEY"] = api_key
    logger.info("Claude model ready")
    return ChatAnthropic(model="claude-sonnet-4-5-20250929")


CLAUDE_MODEL = initialize_claude_model(ANTHROPIC_API_KEY)

ALL_TABLES = [
    "stops",
    "paths",
    "routes",
    "daily_trips",
    "deployments",
    "vehicles",
    "drivers",
]

PAGE_TABLE_ACCESS = {
    "busDashboard": [
        "daily_trips",
        "deployments",
        "vehicles",
        "drivers",
    ],
    "manageRoute": [
        "stops",
        "paths",
        "routes",
        "vehicles",
        "drivers",
    ],
}

TABLE_SCHEMAS = {
    "stops": {
        "primary_key": "stop_id",
        "columns": [
            "stop_id",
            "name",
            "latitude",
            "longitude",
            "description",
            "address",
            "is_active",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
            "deleted_at",
            "deleted_by",
        ],
    },
    "paths": {
        "primary_key": "path_id",
        "columns": [
            "path_id",
            "path_name",
            "ordered_list_of_stop_ids",
            "description",
            "total_distance_km",
            "estimated_duration_minutes",
            "is_active",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
            "deleted_at",
            "deleted_by",
        ],
    },
    "routes": {
        "primary_key": "route_id",
        "columns": [
            "route_id",
            "path_id",
            "route_display_name",
            "shift_time",
            "direction",
            "start_point",
            "end_point",
            "status",
            "notes",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
            "deleted_at",
            "deleted_by",
        ],
    },
    "vehicles": {
        "primary_key": "vehicle_id",
        "columns": [
            "vehicle_id",
            "license_plate",
            "type",
            "capacity",
            "make",
            "model",
            "year",
            "color",
            "registration_date",
            "last_service_date",
            "next_service_date",
            "is_available",
            "status",
            "notes",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
            "deleted_at",
            "deleted_by",
        ],
    },
    "drivers": {
        "primary_key": "driver_id",
        "columns": [
            "driver_id",
            "name",
            "phone_number",
            "email",
            "license_number",
            "license_expiry_date",
            "address",
            "emergency_contact_name",
            "emergency_contact_phone",
            "is_available",
            "status",
            "notes",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
            "deleted_at",
            "deleted_by",
        ],
    },
    "daily_trips": {
        "primary_key": "trip_id",
        "columns": [
            "trip_id",
            "route_id",
            "display_name",
            "trip_date",
            "booking_status_percentage",
            "live_status",
            "scheduled_departure_time",
            "actual_departure_time",
            "scheduled_arrival_time",
            "actual_arrival_time",
            "total_bookings",
            "status",
            "notes",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
            "deleted_at",
            "deleted_by",
        ],
    },
    "deployments": {
        "primary_key": "deployment_id",
        "columns": [
            "deployment_id",
            "trip_id",
            "vehicle_id",
            "driver_id",
            "deployment_status",
            "assigned_at",
            "confirmed_at",
            "notes",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
            "deleted_at",
            "deleted_by",
        ],
    },
}

session_memories: dict[str, dict[str, Any]] = {}

AFFIRM = {"yes", "y", "yeah", "yep", "sure", "ok", "okay", "confirm", "proceed"}
DECLINE = {"no", "n", "nope", "cancel", "stop", "never", "not now"}


def _normalize(text: str) -> str:
    return " ".join(text.lower().split()) if text else ""


def _classify_confirmation(text: str) -> Optional[str]:
    normalized = _normalize(text)
    if not normalized:
        return None
    if normalized in AFFIRM:
        return "yes"
    if normalized in DECLINE:
        return "no"
    return None


def _ensure_memory(session_id: str, page: str) -> dict[str, Any]:
    memory = session_memories.get(session_id)
    if memory and page and memory.get("current_page") != page:
        memory = None
    if not memory:
        session_memories[session_id] = {
            "current_page": page,
            "messages": [],
            "pending_confirmation": None,
        }
        memory = session_memories[session_id]
    return memory


def _save_turn(memory: dict[str, Any], user_text: str, assistant_text: str) -> None:
    memory.setdefault("messages", []).extend(
        [
            {"role": "user", "content": user_text},
            {"role": "assistant", "content": assistant_text},
        ]
    )


def _handle_confirmation(memory: dict[str, Any], user_text: str):
    pending = memory.get("pending_confirmation")
    if not pending:
        return None

    decision = _classify_confirmation(user_text)
    if decision == "yes":
        memory["pending_confirmation"] = None
        return {
            "action": "proceed",
            "ack": pending.get("affirm_ack"),
            "post_action": pending.get("post_action"),
        }
    if decision == "no":
        memory["pending_confirmation"] = None
        return {"action": "stop", "message": pending.get("cancel_text")}

    return {"action": "reprompt", "message": pending.get("reprompt_text")}


def _queue_confirmation(memory: dict[str, Any], warning: ConsequenceWarning) -> str:
    notice = warning.message
    post_action: Optional[dict[str, Any]] = None
    if warning.deployment_id:
        post_action = {
            "type": "remove_deployment",
            "deployment_id": warning.deployment_id,
            "trip_name": warning.trip_name,
        }
    memory["pending_confirmation"] = {
        "trip": warning.trip_name,
        "affirm_ack": (
            f"Confirmed. Proceeding even though '{warning.trip_name}' is "
            f"{int(warning.booking_percentage)}% booked."
        ),
        "cancel_text": (
            f"No problem — keeping the vehicle assigned to '{warning.trip_name}'."
        ),
        "reprompt_text": (
            f"Please reply with 'yes' to remove the vehicle from '{warning.trip_name}' "
            "or 'no' to leave it as-is."
        ),
        "post_action": post_action,
    }
    return notice


def _build_augmented_query(
    user_message: str, vision_result: Optional[VisionExtraction]
) -> str:
    if not vision_result:
        return user_message

    trip = vision_result.trip_name
    action = (vision_result.detected_action or "").lower()
    if trip and action in {"remove_vehicle", "delete_deployment", "unassign_vehicle"}:
        return (
            f"Remove the vehicle from '{trip}'. "
            f"(Screenshot context from user: {user_message})"
        )
    if trip:
        return f"{user_message}\nScreenshot indicates this concerns trip '{trip}'."
    return user_message


def _vision_preface(vision_result: Optional[VisionExtraction]) -> str:
    if not vision_result:
        return ""
    if vision_result.trip_name:
        confidence_pct = int(vision_result.confidence * 100)
        return (
            f"[Vision] Screenshot highlights trip '{vision_result.trip_name}' "
            f"(confidence {confidence_pct}%)."
        )
    return f"[Vision] {vision_result.reasoning}" if vision_result.reasoning else ""


def _perform_post_confirmation_action(
    action_payload: Optional[dict[str, Any]]
) -> tuple[bool, str]:
    if not action_payload:
        return False, "Confirmation acknowledged, but no follow-up action was recorded."

    action_type = action_payload.get("type")
    if action_type == "remove_deployment":
        deployment_id = action_payload.get("deployment_id")
        trip_name = action_payload.get("trip_name") or "this trip"
        if not deployment_id:
            return False, "I couldn't find the deployment record to update."
        try:
            repo = DeploymentsRepository()
            repo.soft_delete(int(deployment_id), deleted_by=SYSTEM_USER_ID)
            return True, f"The vehicle assignment for '{trip_name}' has been removed."
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Failed to soft delete deployment %s: %s", deployment_id, exc)
            return (
                False,
                "I tried to remove the deployment directly, but encountered an unexpected error.",
            )

    return False, "Confirmation recorded, but I don't know how to finish that action automatically."


def _format_tool_exception_message(exc: ToolException) -> str:
    raw = str(exc).strip()
    detail = raw
    try:
        payload = json.loads(raw)
        if isinstance(payload, dict):
            message = (
                payload.get("error", {}).get("message")
                if isinstance(payload.get("error"), dict)
                else None
            )
            if message:
                detail = message
    except (json.JSONDecodeError, TypeError):
        pass

    return (
        "I tried to run that action, but the database rejected the change:\n"
        f"{detail}\n"
        "Please fix the data and try again, or let me know if you want to cancel."
    )


class AgentRequest(BaseModel):
    query: str
    current_page: Optional[str] = None
    session_id: Optional[str] = None


class AgentResponse(BaseModel):
    final_message: Any
    raw_response: str


class ChatRequest(BaseModel):
    message: str
    current_page: Optional[str] = None
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: Any
    session_id: Optional[str] = None


def extract_final_message(response: Any) -> Any:
    messages = response.get("messages") if isinstance(response, dict) else None
    final_message = messages[-1] if messages else None
    if final_message and hasattr(final_message, "content"):
        return final_message.content
    return response


async def run_agent(
    query: str, current_page: Optional[str] = None, session_id: Optional[str] = None
):
    model = CLAUDE_MODEL
    if model is None:
        raise HTTPException(
            status_code=400,
            detail="Claude model is not configured. Check ANTHROPIC_API_KEY.",
        )

    logger.info("Connecting to Supabase MCP server")
    async with streamablehttp_client(SUPABASE_URL, headers=SUPABASE_HEADERS) as (
        read,
        write,
        _,
    ):
        async with ClientSession(read, write) as session:
            logger.info("Initializing MCP session")
            await session.initialize()

            logger.info("Loading MCP tools")
            tools = await load_mcp_tools(session)
            logger.info("Loaded %d tools", len(tools))

            logger.info("Creating ReAct agent with claude")
            agent = create_react_agent(model, tools)

            normalized_page = (current_page or "").strip()
            allowed_tables = PAGE_TABLE_ACCESS.get(normalized_page, ALL_TABLES)
            schema_subset = {
                table: TABLE_SCHEMAS.get(table)
                for table in allowed_tables
                if TABLE_SCHEMAS.get(table)
            }

            history: list[dict[str, str]] = []
            memory: Optional[dict[str, Any]] = None
            confirmation_ack: Optional[str] = None

            if session_id:
                memory = _ensure_memory(session_id, normalized_page)
                memory["current_page"] = normalized_page
                history = list(memory.get("messages", []))

                confirmation_result = _handle_confirmation(memory, query)
                if confirmation_result:
                    if confirmation_result["action"] == "stop":
                        reply = confirmation_result["message"]
                        _save_turn(memory, query, reply)
                        return reply, reply
                    if confirmation_result["action"] == "reprompt":
                        reply = confirmation_result["message"]
                        _save_turn(memory, query, reply)
                        return reply, reply
                    if confirmation_result["action"] == "proceed":
                        post_action = confirmation_result.get("post_action")
                        confirmation_ack = confirmation_result.get("ack")
                        if post_action:
                            success, action_message = _perform_post_confirmation_action(
                                post_action
                            )
                            reply_parts = [
                                part for part in [confirmation_ack, action_message] if part
                            ]
                            reply_text = "\n\n".join(reply_parts) if reply_parts else "Confirmed."
                            if memory is not None:
                                _save_turn(memory, query, reply_text)
                            return reply_text, reply_text

                if confirmation_ack is None:
                    warning = analyze_trip_removal_request(query)
                    if warning:
                        notice = _queue_confirmation(memory, warning)
                        _save_turn(memory, query, notice)
                        return notice, notice

            logger.info(
                "Invoking agent with query: %s (page=%s tables=%s history=%s entries)",
                query,
                normalized_page or "unknown",
                ",".join(allowed_tables),
                len(history),
            )

            context_payload = json.dumps(
                {
                    "page": normalized_page or "unknown",
                    "allowed_tables": allowed_tables,
                    "table_schemas": schema_subset,
                }
            )

            system_message = (
                "You are Movi, the transport assistant. "
                f"Context: {context_payload}. "
                "Rules:\n"
                "1. Only query or mutate tables listed in allowed_tables. "
                "If the user asks for data outside the allowed list, politely ask "
                "them to switch to the appropriate page instead of attempting the action.\n"
                "2. Provide concise, page-aware explanations. Mention when an action "
                "is blocked due to page context and which page would enable it.\n"
                "3. When collecting data for create/update flows, remember prior "
                "answers from this session and only re-ask missing fields.\n"
                "4. Use the provided table_schemas to reference the correct primary keys "
                "and column names. Never assume an 'id' column if the schema specifies "
                "a different primary key.\n"
                "5. Confirm destructive actions only after explaining consequences.\n"
                "Always respond as a helpful transport assistant."
            )

            messages = [{"role": "system", "content": system_message}]
            if history:
                messages.extend(history)
            messages.append({"role": "user", "content": query})

            try:
                response = await agent.ainvoke({"messages": messages})
                final_message = extract_final_message(response)
            except ToolException as exc:
                error_message = _format_tool_exception_message(exc)
                logger.warning("Tool execution failed: %s", exc)
                if memory is not None:
                    _save_turn(memory, query, error_message)
                return error_message, json.dumps(
                    {"error": error_message, "tool_exception": str(exc)}
                )

            response_text = str(final_message)
            if confirmation_ack:
                response_text = f"{confirmation_ack}\n\n{response_text}"

            if memory is not None:
                memory["messages"].extend(
                    [
                        {"role": "user", "content": query},
                        {"role": "assistant", "content": response_text},
                    ]
                )

            return response_text, str(response)


def _build_allowed_origins() -> List[str]:
    """
    Compose the CORS allow-list from sensible defaults plus any values
    supplied through ALLOWED_ORIGINS (comma-separated) or
    platform-specific env vars like RENDER_EXTERNAL_URL.
    """
    defaults = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:5000",
        "https://moveinsync-movi.onrender.com",
    ]

    render_external_url = os.getenv("RENDER_EXTERNAL_URL")
    if render_external_url:
        defaults.append(render_external_url.rstrip("/"))

    env_origins = os.getenv("ALLOWED_ORIGINS", "")
    for origin in env_origins.split(","):
        cleaned = origin.strip().rstrip("/")
        if cleaned:
            defaults.append(cleaned)

    # Preserve order but drop duplicates
    seen = set()
    ordered = []
    for origin in defaults:
        if origin not in seen:
            ordered.append(origin)
            seen.add(origin)
    return ordered


app = FastAPI(title="MCP Supabase Agent API")

allowed_origins = _build_allowed_origins()

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/agent", response_model=AgentResponse)
async def invoke_agent(payload: AgentRequest):
    logger.info("Received agent request")
    final_message, raw_response = await run_agent(
        payload.query, payload.current_page, payload.session_id
    )
    
    return AgentResponse(
        final_message=final_message,
        raw_response=raw_response,
    )


@app.post("/api/chat", response_model=ChatResponse)
async def legacy_chat_endpoint(payload: ChatRequest):
    final_message, _ = await run_agent(
        payload.message, payload.current_page, payload.session_id
    )
    return ChatResponse(
        response=final_message,
        session_id=payload.session_id,
    )

# Legacy CRUD routers exposed so the chatbot backend can continue serving
# the existing frontend endpoints.
app.include_router(stops.router, prefix="/api/stops", tags=["Stops"])
app.include_router(paths.router, prefix="/api/paths", tags=["Paths"])
app.include_router(routes.router, prefix="/api/routes", tags=["Routes"])
app.include_router(vehicles.router, prefix="/api/vehicles", tags=["Vehicles"])
app.include_router(drivers.router, prefix="/api/drivers", tags=["Drivers"])
app.include_router(trips.router, prefix="/api/trips", tags=["Trips"])
app.include_router(deployments.router, prefix="/api/deployments", tags=["Deployments"])


@app.post("/api/upload-image", response_model=ChatResponse)
async def upload_image_endpoint(
    file: UploadFile = File(...),
    message: str = Form(...),
    current_page: Optional[str] = Form(None),
    session_id: Optional[str] = Form(None),
):
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded image is empty.")

    try:
        vision_result = await run_in_threadpool(
            process_dashboard_image, contents, message
        )
    except VisionProcessingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    augmented_query = _build_augmented_query(message, vision_result)
    preface = _vision_preface(vision_result)

    final_message, _ = await run_agent(
        augmented_query, current_page, session_id
    )

    if preface:
        if isinstance(final_message, str):
            final_message = f"{preface}\n\n{final_message}"
        else:
            final_message = f"{preface}\n\n{str(final_message)}"

    return ChatResponse(
        response=final_message,
        session_id=session_id,
    )