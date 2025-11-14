import base64
import json
import logging
import os
from typing import Any, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from langchain_anthropic import ChatAnthropic
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from pydantic import BaseModel
from langchain_core.messages import HumanMessage

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


async def describe_image(image_data: str) -> str:
    if not image_data or CLAUDE_MODEL is None:
        return ""

    prompt = (
        "You are analyzing a screenshot of the Movi transport dashboard. "
        "Identify the current page (busDashboard or manageRoute), the highlighted "
        "trip/route/vehicle, and summarize any markings (arrows, highlights, notes). "
        "Respond with a concise paragraph."
    )

    try:
        response = await CLAUDE_MODEL.ainvoke(
            [
                HumanMessage(
                    content=[
                        {
                            "type": "text",
                            "text": prompt,
                        },
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": image_data,
                            },
                        },
                    ]
                )
            ]
        )
        if hasattr(response, "content"):
            blocks = response.content
            if isinstance(blocks, list):
                texts = []
                for block in blocks:
                    text = block.get("text") if isinstance(block, dict) else None
                    if text:
                        texts.append(text)
                if texts:
                    return "\n".join(texts).strip()
        return extract_final_message(response)
    except Exception as exc:  # noqa: BLE001
        logger.error("Image description failed: %s", exc)
        return ""


class AgentRequest(BaseModel):
    query: str
    current_page: Optional[str] = None
    session_id: Optional[str] = None
    image_data: Optional[str] = None


class AgentResponse(BaseModel):
    final_message: Any
    raw_response: str


class ChatRequest(BaseModel):
    message: str
    current_page: Optional[str] = None
    session_id: Optional[str] = None
    image_data: Optional[str] = None


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
            if session_id:
                memory = session_memories.get(session_id)
                if (
                    memory
                    and normalized_page
                    and memory.get("current_page") != normalized_page
                ):
                    logger.info(
                        "Session %s switched page from %s to %s; resetting memory",
                        session_id,
                        memory.get("current_page"),
                        normalized_page,
                    )
                    memory = None
                    session_memories[session_id] = {
                        "current_page": normalized_page,
                        "messages": [],
                    }

                if not memory:
                    session_memories[session_id] = {
                        "current_page": normalized_page,
                        "messages": [],
                    }
                    memory = session_memories[session_id]

                history = list(memory.get("messages", []))

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

            response = await agent.ainvoke({"messages": messages})
            final_message = extract_final_message(response)

            if session_id:
                memory = session_memories.setdefault(
                    session_id,
                    {"current_page": normalized_page, "messages": []},
                )
                memory["current_page"] = normalized_page
                memory["messages"].extend(
                    [
                        {"role": "user", "content": query},
                        {"role": "assistant", "content": str(final_message)},
                    ]
                )

            return final_message, str(response)


app = FastAPI(title="MCP Supabase Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:5000",
    ],
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