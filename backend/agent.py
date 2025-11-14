"""
LangGraph implementation for Movi transport management AI agent.

This module implements a complete agent workflow with:
- Intent classification using OpenAI GPT-4o function calling
- Image processing for dashboard screenshots
- Consequence checking (Tribal Knowledge)
- User confirmation flow
- Tool execution
"""
from __future__ import annotations

from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, List, Optional, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.tools import tool
import ast
import base64
import json
import logging
import operator
import os
import re
from pathlib import Path
from dotenv import load_dotenv
from database.repositories import PathsRepository, TripsRepository, StopsRepository, RoutesRepository

# Load environment variables
PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

# Logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

OPENAI_TEXT_MODEL = os.getenv("OPENAI_TEXT_MODEL", "gpt-4o-mini")
OPENAI_VISION_MODEL = os.getenv("OPENAI_VISION_MODEL", OPENAI_TEXT_MODEL)
MAX_TOOL_ITEMS_FOR_LLM = 25


def build_openai_llm(model_name: Optional[str] = None) -> ChatOpenAI:
    """Create an OpenAI chat model instance with shared defaults."""
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY not found in environment variables")
    return ChatOpenAI(model=model_name or OPENAI_TEXT_MODEL, temperature=0)


# Multi-turn form configuration for create/update flows
FORM_CONFIG = {
    "create_vehicle": [
        {"field": "license_plate", "prompt": "Please provide the vehicle's license plate (e.g., KA-01-AB-1234)."},
        {"field": "type", "prompt": "What type of vehicle is it? (Bus or Cab)"},
        {"field": "capacity", "prompt": "How many seats does it have?"}
    ],
    "create_driver": [
        {"field": "name", "prompt": "What is the driver's full name?"},
        {"field": "phone_number", "prompt": "What is the driver's phone number?"}
    ],
    "create_stop_record": [
        {"field": "name", "prompt": "What should we name the stop?"},
        {"field": "latitude", "prompt": "What is the latitude? (between -90 and 90)"},
        {"field": "longitude", "prompt": "What is the longitude? (between -180 and 180)"}
    ],
    "create_path_record": [
        {"field": "path_name", "prompt": "What should we name the path?"},
        {"field": "ordered_list_of_stop_ids", "prompt": "Provide stop IDs in order (comma separated, at least two)."}
    ],
    "create_route_record": [
        {"field": "path_id", "prompt": "Which path ID should this route use?"},
        {"field": "shift_time", "prompt": "What shift time? (HH:MM, 24-hour format)"},
        {"field": "direction", "prompt": "Direction? (Forward, Reverse, or Circular)"},
        {"field": "route_display_name", "prompt": "What is the route display name?"}
    ],
    "create_trip": [
        {"field": "route_id", "prompt": "Which route ID should this trip use?"},
        {"field": "display_name", "prompt": "What is the trip display name?"}
    ]
}

def _parse_ordered_ids(value: str) -> List[int]:
    """Convert comma-separated string to list of ints."""
    parts = [p.strip() for p in value.split(",") if p.strip()]
    return [int(p) for p in parts]


def needs_form(tool_name: str, args: Dict[str, Any]) -> bool:
    config = FORM_CONFIG.get(tool_name)
    if not config:
        return False
    for field_cfg in config:
        field = field_cfg["field"]
        if not args.get(field):
            return True
    return False


def next_missing_field(tool_name: str, collected: Dict[str, Any]) -> Optional[Dict[str, str]]:
    config = FORM_CONFIG.get(tool_name, [])
    for field_cfg in config:
        if not collected.get(field_cfg["field"]):
            return field_cfg
    return None


def format_data_preview(data: Any, limit: int = 3) -> str:
    if data is None:
        return ""
    if isinstance(data, list):
        preview_items = data[:limit]
        formatted_items = []
        for item in preview_items:
            if isinstance(item, dict):
                first_fields = list(item.items())[:5]
                formatted_items.append(", ".join(f"{k}: {v}" for k, v in first_fields))
            else:
                formatted_items.append(str(item))
        suffix = "" if len(data) <= limit else f" (showing {limit} of {len(data)})"
        return "\n".join(f"- {entry}" for entry in formatted_items) + suffix
    if isinstance(data, dict):
        first_fields = list(data.items())[:8]
        return "\n".join(f"- {k}: {v}" for k, v in first_fields)
    return str(data)


def parse_literal(value: str) -> Any:
    try:
        return ast.literal_eval(value)
    except Exception:
        return value


def try_parse_tool_command(text: str) -> Optional[Dict[str, Any]]:
    """
    Detect inline tool invocations like:
    ```tool_get_all_vehicles()```
    ```tool_filter_vehicles_by_type
    vehicle_type: bus
    ```
    """
    if not text:
        return None

    cleaned = text.strip().strip("`").strip()
    if not cleaned.startswith("tool_"):
        cleaned = cleaned.replace("`", "").strip()
        if not cleaned.startswith("tool_"):
            # Try regex fallback for inline function-style call
            match = re.search(r"(tool_[a-zA-Z0-9_]+)\s*\((.*?)\)", cleaned, re.DOTALL)
            if not match:
                return None
            tool_name = match.group(1).replace("tool_", "")
            args_str = match.group(2).strip()
            return {
                "tool_name": tool_name,
                "args": _parse_args_from_parentheses(args_str)
            }

    lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
    if not lines:
        return None

    first_line = lines[0]
    # Handle function-style single line e.g. tool_xxx(...)
    if "(" in first_line and ")" in first_line:
        match = re.search(r"(tool_[a-zA-Z0-9_]+)\s*\((.*?)\)", first_line)
        if not match:
            return None
        tool_name = match.group(1).replace("tool_", "")
        args_str = match.group(2).strip()
        return {
            "tool_name": tool_name,
            "args": _parse_args_from_parentheses(args_str)
        }

    # Otherwise treat as block where following lines are key:value pairs
    tool_name = first_line.replace("tool_", "")
    args = _parse_args_from_block(lines[1:])
    return {"tool_name": tool_name, "args": args}


def _parse_args_from_parentheses(args_str: str) -> Dict[str, Any]:
    args: Dict[str, Any] = {}
    if not args_str:
        return args
    if "=" in args_str:
        parts = [p.strip() for p in args_str.split(",") if p.strip()]
        for part in parts:
            if "=" in part:
                key, value = part.split("=", 1)
                args[key.strip()] = parse_literal(value.strip())
    else:
        parsed = parse_literal(args_str)
        if isinstance(parsed, dict):
            args = parsed
        elif parsed is not None:
            args["value"] = parsed
    return args


def _parse_args_from_block(lines: List[str]) -> Dict[str, Any]:
    args: Dict[str, Any] = {}
    buffer_key: Optional[str] = None
    buffer_value_lines: List[str] = []

    def flush_buffer():
        nonlocal buffer_key, buffer_value_lines, args
        if buffer_key is None:
            return
        value_str = "\n".join(buffer_value_lines).strip()
        args[buffer_key] = parse_literal(value_str) if value_str else None
        buffer_key = None
        buffer_value_lines = []

    for line in lines:
        if ":" in line and line.split(":", 1)[0].strip():
            flush_buffer()
            key, value = line.split(":", 1)
            buffer_key = key.strip()
            buffer_value_lines = [value.strip()]
        else:
            buffer_value_lines.append(line.strip())

    flush_buffer()
    return args


def get_last_user_message(state: AgentState) -> str:
    """Return the most recent user utterance."""
    for msg in reversed(state.get("messages", [])):
        if msg.get("role") == "user" and msg.get("content"):
            return msg["content"]
    return ""


def dict_to_message(message: Dict[str, str]) -> Optional[HumanMessage]:
    """Convert stored conversation dicts into LangChain message objects."""
    role = message.get("role")
    content = message.get("content", "")
    if not content:
        return None
    if role == "system":
        return SystemMessage(content=content)
    if role == "assistant":
        return AIMessage(content=content)
    return HumanMessage(content=content)


def serialize_tool_result(result: Dict[str, Any]) -> str:
    """Safely serialize tool results for prompting."""
    try:
        return json.dumps(result, default=str)
    except Exception:
        return str(result)


def prepare_followup_payload(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Trim large tool responses before sending them back to the LLM to avoid token explosions.
    """
    payload = dict(result)
    data = payload.get("data")

    if isinstance(data, list):
        total = len(data)
        if total > MAX_TOOL_ITEMS_FOR_LLM:
            logger.warning(
                "followup payload truncated: %s items -> %s",
                total,
                MAX_TOOL_ITEMS_FOR_LLM,
            )
            payload["data"] = data[:MAX_TOOL_ITEMS_FOR_LLM]
            payload["summary"] = {
                "total_items": total,
                "shown_items": MAX_TOOL_ITEMS_FOR_LLM,
                "note": f"Showing first {MAX_TOOL_ITEMS_FOR_LLM} results. Ask for filters to view more.",
            }
        else:
            payload["summary"] = {"total_items": total}
    elif isinstance(data, dict):
        keys = list(data.keys())[:10]
        payload["summary"] = {"fields_preview": keys}
    else:
        payload["summary"] = {"data_type": type(data).__name__}

    return payload


def generate_llm_followup(state: AgentState, tool_name: str, result: Dict[str, Any]) -> str:
    """
    Run a lightweight OpenAI pass so the LLM formats the tool output before
    responding to the user.
    """
    trimmed_result = prepare_followup_payload(result)
    llm = build_openai_llm()

    user_context = get_last_user_message(state) or "the user's latest request"
    serialized = serialize_tool_result(trimmed_result)
    prompt = (
        "You are Movi, an operations assistant for a transport company.\n"
        "The following JSON came from a trusted tool call. Extract the key facts "
        "and answer the user's request directly. Prefer bullet lists for multiple "
        "items and mention totals. If an error is present, apologize and explain it. "
        "Avoid referencing internal tool names.\n\n"
        f"User request: {user_context}\n"
        f"Tool output:\n{serialized}"
    )

    response = llm.invoke([
        SystemMessage(content="Always provide clear, data-backed answers using the supplied tool output."),
        HumanMessage(content=prompt)
    ])
    return response.content if hasattr(response, "content") else str(response)

# Import all tool functions
from backend.tools import (
    # Vehicle tools
    get_all_vehicles,
    get_vehicle_by_id,
    create_vehicle,
    update_vehicle,
    delete_vehicle,
    filter_vehicles_by_type,
    filter_vehicles_by_availability,
    get_unassigned_vehicles,
    # Driver tools
    get_all_drivers,
    get_driver_by_id,
    create_driver,
    update_driver,
    delete_driver,
    filter_drivers_by_availability,
    get_available_drivers,
    # Stop tools
    get_all_stops,
    get_stop_by_id,
    create_stop_record,
    update_stop,
    delete_stop,
    search_stops_by_name,
    # Route tools
    get_all_routes,
    get_route_by_id,
    create_route_record,
    update_route,
    delete_route,
    filter_routes_by_path,
    filter_routes_by_status,
    filter_routes_by_direction,
    # Path tools
    get_all_paths,
    get_path_by_id,
    create_path_record,
    update_path,
    delete_path,
    filter_paths_by_stop,
    # Trip tools
    get_all_trips,
    get_trip_by_id,
    create_trip,
    update_trip,
    delete_trip,
    filter_trips_by_route,
    filter_trips_by_status,
    update_trip_status,
    filter_trips_by_date,
    get_trip_status,
    get_all_active_trips,
    get_completed_trips_count,
    # Deployment tools
    get_all_deployments,
    get_deployment_by_id,
    create_deployment,
    delete_deployment,
    filter_deployments_by_trip,
    filter_deployments_by_vehicle,
    filter_deployments_by_driver,
    assign_vehicle_to_trip,
    remove_vehicle_from_trip,
    # Legacy stop/path/route tools
    list_stops_for_path,
    get_routes_by_path,
    get_all_active_stops,
    create_stop,
    create_path,
    create_route
)


# ============================================================================
# STATE DEFINITION
# ============================================================================

class AgentState(TypedDict):
    """State definition for the Movi agent workflow"""
    messages: Annotated[List[Dict[str, str]], operator.add]  # Conversation history with role and content
    current_page: str  # Either "busDashboard" or "manageRoute"
    pending_action: Optional[Dict[str, Any]]  # Stores {"tool_name": str, "args": dict}
    consequences: Optional[Dict[str, Any]]  # Stores {"has_consequences": bool, "message": str}
    awaiting_confirmation: bool  # True when waiting for user yes/no response
    image_data: Optional[str]  # Base64 encoded image (if uploaded)
    image_mime_type: Optional[str]  # MIME type of uploaded image (if any)
    form_state: Optional[Dict[str, Any]]  # Tracks multi-turn data collection
    session_id: str  # Unique session identifier


# ============================================================================
# TOOL WRAPPERS (for LangChain function calling)
# ============================================================================

@tool
def tool_get_all_vehicles() -> Dict[str, Any]:
    """List all active vehicles."""
    return get_all_vehicles()


@tool
def tool_get_vehicle_by_id(vehicle_id: int) -> Dict[str, Any]:
    """Get vehicle details by ID."""
    return get_vehicle_by_id(vehicle_id)


@tool
def tool_create_vehicle(vehicle_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new vehicle."""
    return create_vehicle(vehicle_data)


@tool
def tool_update_vehicle(vehicle_id: int, update_data: Dict[str, Any]) -> Dict[str, Any]:
    """Update vehicle fields."""
    return update_vehicle(vehicle_id, update_data)


@tool
def tool_delete_vehicle(vehicle_id: int) -> Dict[str, Any]:
    """Soft delete a vehicle."""
    return delete_vehicle(vehicle_id)


@tool
def tool_filter_vehicles_by_type(vehicle_type: str) -> Dict[str, Any]:
    """Filter vehicles by type."""
    return filter_vehicles_by_type(vehicle_type)


@tool
def tool_filter_vehicles_by_availability(is_available: bool) -> Dict[str, Any]:
    """Filter vehicles by availability."""
    return filter_vehicles_by_availability(is_available)


@tool
def tool_get_all_drivers() -> Dict[str, Any]:
    """List all active drivers."""
    return get_all_drivers()


@tool
def tool_get_driver_by_id(driver_id: int) -> Dict[str, Any]:
    """Get driver details by ID."""
    return get_driver_by_id(driver_id)


@tool
def tool_create_driver(driver_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new driver."""
    return create_driver(driver_data)


@tool
def tool_update_driver(driver_id: int, update_data: Dict[str, Any]) -> Dict[str, Any]:
    """Update driver record."""
    return update_driver(driver_id, update_data)


@tool
def tool_delete_driver(driver_id: int) -> Dict[str, Any]:
    """Soft delete a driver."""
    return delete_driver(driver_id)


@tool
def tool_filter_drivers_by_availability(is_available: bool) -> Dict[str, Any]:
    """Filter drivers by availability."""
    return filter_drivers_by_availability(is_available)


@tool
def tool_get_all_stops() -> Dict[str, Any]:
    """List all active stops."""
    return get_all_stops()


@tool
def tool_get_stop_by_id(stop_id: int) -> Dict[str, Any]:
    """Get stop details by ID."""
    return get_stop_by_id(stop_id)


@tool
def tool_create_stop_record(stop_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new stop using structured data."""
    return create_stop_record(stop_data)


@tool
def tool_update_stop(stop_id: int, update_data: Dict[str, Any]) -> Dict[str, Any]:
    """Update stop fields."""
    return update_stop(stop_id, update_data)


@tool
def tool_delete_stop(stop_id: int) -> Dict[str, Any]:
    """Soft delete a stop."""
    return delete_stop(stop_id)


@tool
def tool_search_stops_by_name(query: str) -> Dict[str, Any]:
    """Search stops by partial name."""
    return search_stops_by_name(query)


@tool
def tool_get_all_routes() -> Dict[str, Any]:
    """List all active routes."""
    return get_all_routes()


@tool
def tool_get_route_by_id(route_id: int) -> Dict[str, Any]:
    """Get route details by ID."""
    return get_route_by_id(route_id)


@tool
def tool_create_route_record(route_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new route using structured data."""
    return create_route_record(route_data)


@tool
def tool_update_route(route_id: int, update_data: Dict[str, Any]) -> Dict[str, Any]:
    """Update route fields."""
    return update_route(route_id, update_data)


@tool
def tool_delete_route(route_id: int) -> Dict[str, Any]:
    """Soft delete a route."""
    return delete_route(route_id)


@tool
def tool_filter_routes_by_path(path_id: int) -> Dict[str, Any]:
    """Filter routes by path."""
    return filter_routes_by_path(path_id)


@tool
def tool_filter_routes_by_status(status: str) -> Dict[str, Any]:
    """Filter routes by status."""
    return filter_routes_by_status(status)


@tool
def tool_filter_routes_by_direction(direction: str) -> Dict[str, Any]:
    """Filter routes by direction."""
    return filter_routes_by_direction(direction)


@tool
def tool_get_all_paths() -> Dict[str, Any]:
    """List all active paths."""
    return get_all_paths()


@tool
def tool_get_path_by_id(path_id: int) -> Dict[str, Any]:
    """Get path details by ID."""
    return get_path_by_id(path_id)


@tool
def tool_create_path_record(path_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new path from structured data."""
    return create_path_record(path_data)


@tool
def tool_update_path(path_id: int, update_data: Dict[str, Any]) -> Dict[str, Any]:
    """Update path fields."""
    return update_path(path_id, update_data)


@tool
def tool_delete_path(path_id: int) -> Dict[str, Any]:
    """Soft delete a path."""
    return delete_path(path_id)


@tool
def tool_filter_paths_by_stop(stop_id: int) -> Dict[str, Any]:
    """Filter paths by stop."""
    return filter_paths_by_stop(stop_id)


@tool
def tool_get_unassigned_vehicles() -> Dict[str, Any]:
    """Get all vehicles that are not currently assigned to any active deployment."""
    return get_unassigned_vehicles()


@tool
def tool_get_available_drivers() -> Dict[str, Any]:
    """Get all drivers that are not currently assigned to any active deployment."""
    return get_available_drivers()


@tool
def tool_get_all_trips() -> Dict[str, Any]:
    """List all active trips."""
    return get_all_trips()


@tool
def tool_get_trip_by_id(trip_id: int) -> Dict[str, Any]:
    """Get trip details by ID."""
    return get_trip_by_id(trip_id)


@tool
def tool_create_trip(trip_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new trip."""
    return create_trip(trip_data)


@tool
def tool_update_trip(trip_id: int, update_data: Dict[str, Any]) -> Dict[str, Any]:
    """Update trip details."""
    return update_trip(trip_id, update_data)


@tool
def tool_delete_trip(trip_id: int) -> Dict[str, Any]:
    """Soft delete a trip."""
    return delete_trip(trip_id)


@tool
def tool_filter_trips_by_route(route_id: int) -> Dict[str, Any]:
    """Filter trips by route."""
    return filter_trips_by_route(route_id)


@tool
def tool_filter_trips_by_status(status: str) -> Dict[str, Any]:
    """Filter trips by status."""
    return filter_trips_by_status(status)


@tool
def tool_update_trip_status(trip_id: int, status: str) -> Dict[str, Any]:
    """Update trip status."""
    return update_trip_status(trip_id, status)


@tool
def tool_filter_trips_by_date(trip_date: str) -> Dict[str, Any]:
    """Filter trips by trip_date."""
    return filter_trips_by_date(trip_date)


@tool
def tool_get_trip_status(trip_identifier: str) -> Dict[str, Any]:
    """Get trip by display_name or trip_id, including booking_status_percentage."""
    return get_trip_status(trip_identifier)


@tool
def tool_list_stops_for_path(path_identifier: str) -> Dict[str, Any]:
    """Get path by name or ID, then get all stops from ordered_list_of_stop_ids."""
    return list_stops_for_path(path_identifier)


@tool
def tool_get_routes_by_path(path_identifier: str) -> Dict[str, Any]:
    """Get all routes where path_id matches the given path identifier."""
    return get_routes_by_path(path_identifier)


@tool
def tool_get_all_active_stops() -> Dict[str, Any]:
    """Get all stops where deleted_at IS NULL."""
    return get_all_active_stops()


@tool
def tool_get_all_active_trips() -> Dict[str, Any]:
    """Get all daily_trips where deleted_at IS NULL."""
    return get_all_active_trips()


@tool
def tool_get_completed_trips_count() -> Dict[str, Any]:
    """Get the count of trips whose status is 'completed'."""
    return get_completed_trips_count()


@tool
def tool_get_all_deployments() -> Dict[str, Any]:
    """List all active deployments."""
    return get_all_deployments()


@tool
def tool_get_deployment_by_id(deployment_id: int) -> Dict[str, Any]:
    """Get deployment details by ID."""
    return get_deployment_by_id(deployment_id)


@tool
def tool_create_deployment(deployment_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a deployment."""
    return create_deployment(deployment_data)


@tool
def tool_delete_deployment(deployment_id: int) -> Dict[str, Any]:
    """Soft delete a deployment."""
    return delete_deployment(deployment_id)


@tool
def tool_filter_deployments_by_trip(trip_id: int) -> Dict[str, Any]:
    """Filter deployments by trip."""
    return filter_deployments_by_trip(trip_id)


@tool
def tool_filter_deployments_by_vehicle(vehicle_id: int) -> Dict[str, Any]:
    """Filter deployments by vehicle."""
    return filter_deployments_by_vehicle(vehicle_id)


@tool
def tool_filter_deployments_by_driver(driver_id: int) -> Dict[str, Any]:
    """Filter deployments by driver."""
    return filter_deployments_by_driver(driver_id)


@tool
def tool_assign_vehicle_to_trip(vehicle_id: str, driver_id: str, trip_id: str) -> Dict[str, Any]:
    """Create a deployment record to assign a vehicle and driver to a trip."""
    return assign_vehicle_to_trip(vehicle_id, driver_id, trip_id)


@tool
def tool_remove_vehicle_from_trip(trip_id: str) -> Dict[str, Any]:
    """Soft delete deployment where trip_id matches."""
    return remove_vehicle_from_trip(trip_id)


@tool
def tool_create_stop(name: str, latitude: float, longitude: float, description: Optional[str] = None, address: Optional[str] = None) -> Dict[str, Any]:
    """Create a new stop with name, coordinates, and optional description/address."""
    return create_stop(name, latitude, longitude, description, address)


@tool
def tool_create_path(name: str, stop_ids: List[int], description: Optional[str] = None, total_distance_km: Optional[float] = None, estimated_duration_minutes: Optional[int] = None) -> Dict[str, Any]:
    """Create a new path with ordered_list_of_stop_ids."""
    return create_path(name, stop_ids, description, total_distance_km, estimated_duration_minutes)


@tool
def tool_create_route(path_id: str, shift_time: str, direction: str, route_display_name: str, start_point: Optional[str] = None, end_point: Optional[str] = None, status: str = "active", notes: Optional[str] = None) -> Dict[str, Any]:
    """Create a new route with path_id, shift_time, direction, and route_display_name."""
    return create_route(path_id, shift_time, direction, route_display_name, start_point, end_point, status, notes)


# List of all tools for binding to LLM
TOOLS = [
    # Vehicle tools
    tool_get_all_vehicles,
    tool_get_vehicle_by_id,
    tool_create_vehicle,
    tool_update_vehicle,
    tool_delete_vehicle,
    tool_filter_vehicles_by_type,
    tool_filter_vehicles_by_availability,
    tool_get_unassigned_vehicles,
    # Driver tools
    tool_get_all_drivers,
    tool_get_driver_by_id,
    tool_create_driver,
    tool_update_driver,
    tool_delete_driver,
    tool_filter_drivers_by_availability,
    tool_get_available_drivers,
    # Stop tools
    tool_get_all_stops,
    tool_get_stop_by_id,
    tool_create_stop_record,
    tool_update_stop,
    tool_delete_stop,
    tool_search_stops_by_name,
    # Route tools
    tool_get_all_routes,
    tool_get_route_by_id,
    tool_create_route_record,
    tool_update_route,
    tool_delete_route,
    tool_filter_routes_by_path,
    tool_filter_routes_by_status,
    tool_filter_routes_by_direction,
    tool_get_all_paths,
    tool_get_path_by_id,
    tool_create_path_record,
    tool_update_path,
    tool_delete_path,
    tool_filter_paths_by_stop,
    # Trip tools
    tool_get_all_trips,
    tool_get_trip_by_id,
    tool_create_trip,
    tool_update_trip,
    tool_delete_trip,
    tool_filter_trips_by_route,
    tool_filter_trips_by_status,
    tool_update_trip_status,
    tool_filter_trips_by_date,
    tool_get_trip_status,
    tool_get_all_active_trips,
    tool_get_completed_trips_count,
    # Deployment tools
    tool_get_all_deployments,
    tool_get_deployment_by_id,
    tool_create_deployment,
    tool_delete_deployment,
    tool_filter_deployments_by_trip,
    tool_filter_deployments_by_vehicle,
    tool_filter_deployments_by_driver,
    tool_assign_vehicle_to_trip,
    tool_remove_vehicle_from_trip,
    # Legacy stop/path/route tools
    tool_list_stops_for_path,
    tool_get_routes_by_path,
    tool_get_all_active_stops,
    tool_create_stop,
    tool_create_path,
    tool_create_route
]


# ============================================================================
# NODE FUNCTIONS
# ============================================================================

def agent_entry_node(state: AgentState) -> AgentState:
    """
    Entry point that routes based on current state.
    Handles confirmation responses and routes to appropriate next node.
    """
    try:
        logger.debug(
            "agent_entry_node called | awaiting_confirmation=%s messages=%d",
            state.get("awaiting_confirmation"),
            len(state.get("messages", [])),
        )
        # Handle multi-turn form responses
        form_state = state.get("form_state")
        if form_state:
            user_message = next((msg.get("content", "") for msg in reversed(state.get("messages", [])) if msg.get("role") == "user"), "")
            if not user_message:
                return state

            if any(word in user_message.lower() for word in ["cancel", "stop", "nevermind", "abort"]):
                logger.info("agent_entry_node: user cancelled form for %s", form_state.get("tool_name"))
                state["form_state"] = None
                state["messages"].append({
                    "role": "assistant",
                    "content": "Form entry cancelled. Let me know if you'd like to start again."
                })
                return state

            current_field_cfg = next_missing_field(form_state["tool_name"], form_state["collected"])
            if current_field_cfg:
                field = current_field_cfg["field"]
                value = user_message.strip()
                if field == "ordered_list_of_stop_ids":
                    try:
                        form_state["collected"][field] = _parse_ordered_ids(value)
                    except Exception:
                        state["messages"].append({
                            "role": "assistant",
                            "content": "Please provide stop IDs as comma-separated numbers (e.g., 1, 2, 3)."
                        })
                        return state
                else:
                    form_state["collected"][field] = value

            next_field_cfg = next_missing_field(form_state["tool_name"], form_state["collected"])
            if next_field_cfg:
                prompt = next_field_cfg["prompt"]
                state["messages"].append({
                    "role": "assistant",
                    "content": prompt
                })
                logger.info("agent_entry_node: asking next form question '%s'", prompt)
                return state
            else:
                state["pending_action"] = {
                    "tool_name": form_state["tool_name"],
                    "args": form_state["collected"]
                }
                logger.info("agent_entry_node: collected all form fields for %s", form_state["tool_name"])
                state["form_state"] = None
                state["messages"].append({
                    "role": "assistant",
                    "content": "Thanks! I have all the details. Executing your request now."
                })

        # Check if we're awaiting confirmation
        if state.get("awaiting_confirmation", False):
            if not state.get("messages"):
                logger.warning("agent_entry_node: awaiting confirmation but no messages present")
                return state
            
            last_message = state["messages"][-1]
            last_content = last_message.get("content", "").lower()
            
            # Check for yes/no response
            if "yes" in last_content or "yep" in last_content or "yeah" in last_content or "confirm" in last_content:
                # User confirmed - keep pending_action, proceed to execution
                state["awaiting_confirmation"] = False
                logger.info("agent_entry_node: user confirmed pending action")
                return state
            
            elif "no" in last_content or "nope" in last_content or "cancel" in last_content:
                # User cancelled - clear pending_action
                state["pending_action"] = None
                state["consequences"] = None
                state["awaiting_confirmation"] = False
                state["messages"].append({
                    "role": "assistant",
                    "content": "Action cancelled. How can I help you?"
                })
                return state
        
        # If not awaiting confirmation, state passes through unchanged
        return state
        
    except Exception as e:
        print(f"Error in agent_entry_node: {str(e)}")
        state["messages"].append({
            "role": "assistant",
            "content": f"Sorry, I encountered an error: {str(e)}"
        })
        return state


def process_image_node(state: AgentState) -> AgentState:
    """
    Extract trip information from uploaded dashboard screenshots using OpenAI vision models.
    Only runs if image_data exists in state.
    """
    try:
        logger.info("process_image_node: image_data_present=%s", bool(state.get("image_data")))
        # Check if image data exists
        if not state.get("image_data"):
            return state
        
        image_data = state["image_data"]
        if not image_data:
            return state
        
        # Prepare LLM for vision prompt
        llm = build_openai_llm(OPENAI_VISION_MODEL)
        
        mime_type = state.get("image_mime_type") or "image/png"
        data_url = f"data:{mime_type};base64,{image_data}"
        
        prompt = (
            "This is a screenshot of a bus dashboard showing trips. "
            "Extract the trip name that is highlighted, circled, or has an arrow pointing to it. "
            "The trip name format is like 'Bulk - 00:01' or 'Path Path - 00:02'. "
            "Return ONLY the exact trip name, nothing else."
        )
        
        message = HumanMessage(content=[
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": data_url}},
        ])
        
        response = llm.invoke([message])
        logger.debug("process_image_node: vision response received")
        
        extracted_trip = ""
        if isinstance(response.content, list):
            extracted_trip = "\n".join(
                part.get("text", "")
                for part in response.content
                if isinstance(part, dict) and part.get("type") == "text"
            ).strip()
        else:
            extracted_trip = str(response.content or "").strip()
        
        # Get last user message and replace references
        if state.get("messages"):
            last_user_message = None
            for msg in reversed(state["messages"]):
                if msg.get("role") == "user":
                    last_user_message = msg
                    break
            
            if last_user_message:
                content = last_user_message.get("content", "")
                # Replace common references with extracted trip name
                content = content.replace("this trip", extracted_trip)
                content = content.replace("the trip", extracted_trip)
                content = content.replace("that trip", extracted_trip)
                # Update the message
                last_user_message["content"] = content
        
        # Clear image data
        state["image_data"] = None
        state["image_mime_type"] = None
        
        return state
        
    except Exception as e:
        logger.exception("process_image_node error: %s", str(e))
        state["messages"].append({
            "role": "assistant",
            "content": f"Sorry, I couldn't process the image: {str(e)}"
        })
        state["image_data"] = None  # Clear image data even on error
        state["image_mime_type"] = None
        return state


def classify_intent_node(state: AgentState) -> AgentState:
    """
    Use OpenAI with function calling to understand user intent and determine which tool to call.
    """
    try:
        logger.info("classify_intent_node: current_page=%s messages=%d",
                    state.get("current_page"), len(state.get("messages", [])))
        # Initialize OpenAI LLM
        llm = build_openai_llm()
        
        # Bind tools to LLM
        llm_with_tools = llm.bind_tools(TOOLS)
        
        # Build messages for LLM
        messages = []
        
        # System message
        current_page = state.get("current_page", "busDashboard")
        system_message = f"You are Movi, a transport management assistant. Current page: {current_page}. Help users manage their transport operations. Use the available tools to perform actions."
        messages.append(SystemMessage(content=system_message))
        
        # Add conversation history as LangChain messages
        for msg in state.get("messages", []):
            lc_msg = dict_to_message(msg)
            if lc_msg:
                messages.append(lc_msg)
        
        # Invoke LLM
        response = llm_with_tools.invoke(messages)
        
        # Check if response has tool calls
        if hasattr(response, "tool_calls") and response.tool_calls:
            # Extract first tool call
            tool_call = response.tool_calls[0]
            state["pending_action"] = {
                "tool_name": tool_call["name"].replace("tool_", ""),  # Remove "tool_" prefix
                "args": tool_call.get("args", {})
            }
            logger.info("classify_intent_node: selected tool=%s args=%s",
                        state["pending_action"]["tool_name"], state["pending_action"]["args"])

            # Handle multi-turn forms for missing fields
            tool_name = state["pending_action"]["tool_name"]
            args = state["pending_action"]["args"] or {}
            if needs_form(tool_name, args):
                field_cfg = next_missing_field(tool_name, args)
                state["form_state"] = {
                    "tool_name": tool_name,
                    "fields": FORM_CONFIG[tool_name],
                    "collected": args.copy(),
                    "initial_args": args.copy()
                }
                prompt = field_cfg["prompt"]
                state["messages"].append({
                    "role": "assistant",
                    "content": prompt
                })
                state["pending_action"] = None
                logger.info("classify_intent_node: initiating form for %s asking '%s'", tool_name, prompt)
                return state
        else:
            # No tool calls - add response text as assistant message
            response_content = response.content if hasattr(response, "content") else str(response)
            parsed_tool = try_parse_tool_command(response_content)
            if parsed_tool:
                logger.info("classify_intent_node: parsed inline tool %s args=%s",
                            parsed_tool["tool_name"], parsed_tool["args"])
                state["pending_action"] = parsed_tool
                state["messages"].append({
                    "role": "assistant",
                    "content": "Sure, pulling that information now."
                })
            else:
                state["messages"].append({
                    "role": "assistant",
                    "content": response_content
                })
                logger.info("classify_intent_node: no tool call, responded directly")
        
        return state
        
    except Exception as e:
        logger.exception("classify_intent_node error: %s", str(e))
        state["messages"].append({
            "role": "assistant",
            "content": f"Sorry, I encountered an error understanding your request: {str(e)}"
        })
        return state


def check_consequences_node(state: AgentState) -> AgentState:
    """
    CRITICAL: Implements "Tribal Knowledge" by checking database for impact before executing actions.
    Checks if removing a vehicle from a trip will affect bookings.
    """
    try:
        pending_action = state.get("pending_action")
        if not pending_action:
            state["consequences"] = {"has_consequences": False}
            return state
        
        tool_name = pending_action.get("tool_name", "")
        logger.info("check_consequences_node: tool=%s args=%s", tool_name, pending_action.get("args"))
        
        # Only check for dangerous operations
        dangerous_operations = [
            "remove_vehicle_from_trip",
            "update_trip_status",
            "delete_route",
            "delete_stop",
        ]
        
        if tool_name == "remove_vehicle_from_trip":
            # Get trip_id from args
            args = pending_action.get("args", {})
            trip_id = args.get("trip_id")
            
            if not trip_id:
                state["consequences"] = {"has_consequences": False}
                return state
            
            # Get trip status to check booking percentage
            trip_result = get_trip_status(str(trip_id))
            
            if trip_result.get("success"):
                trip_data = trip_result.get("data", {})
                booking_percentage = trip_data.get("booking_status_percentage", 0.0) or 0.0
                
                if booking_percentage > 0:
                    # Has bookings - warn user
                    trip_name = trip_data.get("display_name", f"Trip {trip_id}")
                    state["consequences"] = {
                        "has_consequences": True,
                        "message": f"⚠️ Trip '{trip_name}' is {booking_percentage}% booked. Removing the vehicle will cancel these bookings and break trip-sheet generation."
                    }
                    logger.info("check_consequences_node: remove_vehicle warning bookings=%s trip=%s",
                                booking_percentage, trip_name)
                else:
                    # No bookings - safe to proceed
                    state["consequences"] = {"has_consequences": False}
            else:
                # Couldn't get trip status - assume safe
                state["consequences"] = {"has_consequences": False}
        elif tool_name == "update_trip_status":
            args = pending_action.get("args", {})
            trip_id = args.get("trip_id")
            status = (args.get("status") or "").lower()
            if not trip_id or status != "cancelled":
                state["consequences"] = {"has_consequences": False}
                return state
            trip_result = get_trip_status(str(trip_id))
            if trip_result.get("success"):
                trip_data = trip_result.get("data", {})
                booking_percentage = trip_data.get("booking_status_percentage", 0.0) or 0.0
                trip_name = trip_data.get("display_name", f"Trip {trip_id}")
                if booking_percentage > 0:
                    state["consequences"] = {
                        "has_consequences": True,
                        "message": f"⚠️ Trip '{trip_name}' is {booking_percentage}% booked. Cancelling it will impact existing bookings. Proceed?",
                    }
                    logger.info("check_consequences_node: trip cancel warning trip=%s bookings=%s",
                                trip_name, booking_percentage)
                else:
                    state["consequences"] = {"has_consequences": False}
            else:
                state["consequences"] = {"has_consequences": False}
        elif tool_name == "delete_route":
            args = pending_action.get("args", {})
            route_id = args.get("route_id")
            if not route_id:
                state["consequences"] = {"has_consequences": False}
                return state
            trips_repo = TripsRepository()
            trips = trips_repo.get_all_active()
            affected = [t for t in trips if t.get("route_id") == int(route_id)]
            if affected:
                state["consequences"] = {
                    "has_consequences": True,
                    "message": f"⚠️ Route {route_id} has {len(affected)} active trips. Deleting it will affect those trips. Proceed?",
                }
                logger.info("check_consequences_node: delete_route warning route=%s trips=%d",
                            route_id, len(affected))
            else:
                state["consequences"] = {"has_consequences": False}
        elif tool_name == "delete_stop":
            args = pending_action.get("args", {})
            stop_id = args.get("stop_id")
            if not stop_id:
                state["consequences"] = {"has_consequences": False}
                return state
            paths_repo = PathsRepository()
            stops_repo = StopsRepository()
            stop = stops_repo.get_by_id(int(stop_id))
            paths = paths_repo.get_all_active()
            affected = [p for p in paths if int(stop_id) in (p.get("ordered_list_of_stop_ids") or [])]
            if affected:
                stop_name = stop.get("name") if stop else f"Stop {stop_id}"
                state["consequences"] = {
                    "has_consequences": True,
                    "message": f"⚠️ {stop_name} is used in {len(affected)} active paths. Deleting it will affect those paths. Proceed?",
                }
                logger.info("check_consequences_node: delete_stop warning stop=%s paths=%d",
                            stop_id, len(affected))
            else:
                state["consequences"] = {"has_consequences": False}
        elif tool_name == "delete_path":
            args = pending_action.get("args", {})
            path_id = args.get("path_id")
            if not path_id:
                state["consequences"] = {"has_consequences": False}
                return state
            routes_repo = RoutesRepository()
            routes = routes_repo.get_all_active()
            affected = [r for r in routes if r.get("path_id") == int(path_id)]
            if affected:
                state["consequences"] = {
                    "has_consequences": True,
                    "message": f"⚠️ Path {path_id} is used by {len(affected)} active routes. Deleting it will affect those routes. Proceed?",
                }
                logger.info("check_consequences_node: delete_path warning path=%s routes=%d",
                            path_id, len(affected))
            else:
                state["consequences"] = {"has_consequences": False}
        else:
            # Not a dangerous operation - safe to proceed
            state["consequences"] = {"has_consequences": False}
        
        return state
        
    except Exception as e:
        print(f"Error in check_consequences_node: {str(e)}")
        # On error, assume safe to proceed
        state["consequences"] = {"has_consequences": False}
        return state


def get_confirmation_node(state: AgentState) -> AgentState:
    """
    Ask user for confirmation before executing dangerous action.
    Sets awaiting_confirmation flag and adds confirmation message.
    """
    try:
        state["awaiting_confirmation"] = True
        
        consequences = state.get("consequences", {})
        consequence_message = consequences.get("message", "This action may have consequences.")
        
        # Build confirmation message
        message = f"I can perform this action. However, {consequence_message} Do you want to proceed? (Reply 'yes' or 'no')"
        logger.info("get_confirmation_node: awaiting user confirmation | message=%s", consequence_message)
        
        # Append to messages
        state["messages"].append({
            "role": "assistant",
            "content": message
        })
        
        return state
        
    except Exception as e:
        print(f"Error in get_confirmation_node: {str(e)}")
        state["messages"].append({
            "role": "assistant",
            "content": f"Sorry, I encountered an error: {str(e)}"
        })
        state["awaiting_confirmation"] = False
        return state


def execute_action_node(state: AgentState) -> AgentState:
    """
    Execute the database operation by calling the tool function.
    Handles tool execution and builds response message.
    """
    try:
        pending_action = state.get("pending_action")
        if not pending_action:
            state["messages"].append({
                "role": "assistant",
                "content": "No action to execute."
            })
            return state
        
        tool_name = pending_action.get("tool_name", "")
        args = pending_action.get("args", {})
        
        # Map tool names to actual functions (remove "tool_" prefix if present)
        tool_name_clean = tool_name.replace("tool_", "")
        logger.info("execute_action_node: tool=%s args=%s", tool_name_clean, args)
        
        # Get tool function dynamically
        tool_functions = {
            # Vehicle tools
            "get_all_vehicles": get_all_vehicles,
            "get_vehicle_by_id": get_vehicle_by_id,
            "create_vehicle": create_vehicle,
            "update_vehicle": update_vehicle,
            "delete_vehicle": delete_vehicle,
            "filter_vehicles_by_type": filter_vehicles_by_type,
            "filter_vehicles_by_availability": filter_vehicles_by_availability,
            "get_unassigned_vehicles": get_unassigned_vehicles,
            # Driver tools
            "get_all_drivers": get_all_drivers,
            "get_driver_by_id": get_driver_by_id,
            "create_driver": create_driver,
            "update_driver": update_driver,
            "delete_driver": delete_driver,
            "filter_drivers_by_availability": filter_drivers_by_availability,
            "get_available_drivers": get_available_drivers,
            # Stop tools
            "get_all_stops": get_all_stops,
            "get_stop_by_id": get_stop_by_id,
            "create_stop_record": create_stop_record,
            "update_stop": update_stop,
            "delete_stop": delete_stop,
            "search_stops_by_name": search_stops_by_name,
            # Route tools
            "get_all_routes": get_all_routes,
            "get_route_by_id": get_route_by_id,
            "create_route_record": create_route_record,
            "update_route": update_route,
            "delete_route": delete_route,
            "filter_routes_by_path": filter_routes_by_path,
            "filter_routes_by_status": filter_routes_by_status,
            "filter_routes_by_direction": filter_routes_by_direction,
            # Path tools
            "get_all_paths": get_all_paths,
            "get_path_by_id": get_path_by_id,
            "create_path_record": create_path_record,
            "update_path": update_path,
            "delete_path": delete_path,
            "filter_paths_by_stop": filter_paths_by_stop,
            # Path tools
            "get_all_paths": get_all_paths,
            "get_path_by_id": get_path_by_id,
            "create_path_record": create_path_record,
            "update_path": update_path,
            "delete_path": delete_path,
            "filter_paths_by_stop": filter_paths_by_stop,
            # Trip tools
            "get_all_trips": get_all_trips,
            "get_trip_by_id": get_trip_by_id,
            "create_trip": create_trip,
            "update_trip": update_trip,
            "delete_trip": delete_trip,
            "filter_trips_by_route": filter_trips_by_route,
            "filter_trips_by_status": filter_trips_by_status,
            "update_trip_status": update_trip_status,
            "filter_trips_by_date": filter_trips_by_date,
            "get_trip_status": get_trip_status,
            "get_all_active_trips": get_all_active_trips,
            "get_completed_trips_count": get_completed_trips_count,
            # Deployment tools
            "get_all_deployments": get_all_deployments,
            "get_deployment_by_id": get_deployment_by_id,
            "create_deployment": create_deployment,
            "delete_deployment": delete_deployment,
            "filter_deployments_by_trip": filter_deployments_by_trip,
            "filter_deployments_by_vehicle": filter_deployments_by_vehicle,
            "filter_deployments_by_driver": filter_deployments_by_driver,
            "assign_vehicle_to_trip": assign_vehicle_to_trip,
            "remove_vehicle_from_trip": remove_vehicle_from_trip,
            # Legacy stop/path/route tools
            "list_stops_for_path": list_stops_for_path,
            "get_routes_by_path": get_routes_by_path,
            "get_all_active_stops": get_all_active_stops,
            "create_stop": create_stop,
            "create_path": create_path,
            "create_route": create_route,
        }
        
        tool_func = tool_functions.get(tool_name_clean)
        if not tool_func:
            state["messages"].append({
                "role": "assistant",
                "content": f"❌ Error: Unknown tool '{tool_name}'"
            })
            # Reset state
            state["pending_action"] = None
            state["consequences"] = None
            state["awaiting_confirmation"] = False
            logger.error("execute_action_node: unknown tool %s", tool_name_clean)
            return state
        
        # Execute tool function
        result = tool_func(**args)
        logger.info("execute_action_node: tool %s success=%s", tool_name_clean, result.get("success"))

        # Route tool output back through OpenAI for the final reply
        try:
            assistant_reply = generate_llm_followup(state, tool_name_clean, result)
        except Exception as followup_error:
            logger.exception("execute_action_node: follow-up generation failed | error=%s",
                             str(followup_error))
            if result.get("success"):
                assistant_reply = result.get("message", "Action completed successfully")
            else:
                assistant_reply = f"❌ Error: {result.get('error', 'Unknown error')}"
        
        # Append to messages
        state["messages"].append({
            "role": "assistant",
            "content": assistant_reply
        })
        
        # Reset state
        state["pending_action"] = None
        state["consequences"] = None
        state["awaiting_confirmation"] = False
        
        return state
        
    except Exception as e:
        print(f"Error in execute_action_node: {str(e)}")
        state["messages"].append({
            "role": "assistant",
            "content": f"❌ Error executing action: {str(e)}"
        })
        # Reset state even on error
        state["pending_action"] = None
        state["consequences"] = None
        state["awaiting_confirmation"] = False
        return state


# ============================================================================
# ROUTER FUNCTIONS (for conditional edges)
# ============================================================================

def route_from_entry(state: AgentState) -> str:
    """Route from agent_entry node based on state conditions."""
    try:
        # If collecting form data, stay in entry node
        if state.get("form_state"):
            return END
        # Check for image data first
        if state.get("image_data"):
            return "process_image"
        
        # Check if awaiting confirmation
        if state.get("awaiting_confirmation", False):
            if not state.get("messages"):
                return "classify_intent"
            
            last_msg = state["messages"][-1]
            last_content = last_msg.get("content", "").lower()
            
            if "yes" in last_content or "yep" in last_content or "yeah" in last_content or "confirm" in last_content:
                return "execute_action"
            elif "no" in last_content or "nope" in last_content or "cancel" in last_content:
                return END
        
        # Default: classify intent
        return "classify_intent"
        
    except Exception as e:
        logger.exception("route_from_entry error: %s", str(e))
        return "classify_intent"


def route_from_classify(state: AgentState) -> str:
    """Route from classify_intent node based on pending_action."""
    try:
        pending_action = state.get("pending_action")
        
        # If no pending action, end
        if not pending_action:
            return END
        
        # Check if action requires consequence checking
        tool_name = pending_action.get("tool_name", "")
        dangerous_operations = ["remove_vehicle_from_trip", "update_trip_status", "delete_route", "delete_stop", "delete_path"]
        
        if tool_name in dangerous_operations:
            return "check_consequences"
        
        # Otherwise, execute directly
        return "execute_action"
        
    except Exception as e:
        logger.exception("route_from_classify error: %s", str(e))
        return END


def route_from_consequences(state: AgentState) -> str:
    """Route from check_consequences node based on consequences."""
    try:
        consequences = state.get("consequences", {})
        
        if consequences.get("has_consequences", False):
            return "get_confirmation"
        
        # No consequences, execute directly
        return "execute_action"
        
    except Exception as e:
        logger.exception("route_from_consequences error: %s", str(e))
        return "execute_action"


# ============================================================================
# BUILD LANGGRAPH
# ============================================================================

def build_agent_graph():
    """
    Build and compile the LangGraph workflow for the Movi agent.
    
    Returns:
        CompiledGraph: The compiled LangGraph workflow
    """
    # Create workflow
    workflow = StateGraph(AgentState)
    
    # Add all nodes
    workflow.add_node("agent_entry", agent_entry_node)
    workflow.add_node("process_image", process_image_node)
    workflow.add_node("classify_intent", classify_intent_node)
    workflow.add_node("check_consequences", check_consequences_node)
    workflow.add_node("get_confirmation", get_confirmation_node)
    workflow.add_node("execute_action", execute_action_node)
    
    # Set entry point
    workflow.set_entry_point("agent_entry")
    
    # Add conditional edges from agent_entry
    workflow.add_conditional_edges(
        "agent_entry",
        route_from_entry,
        {
            "process_image": "process_image",
            "classify_intent": "classify_intent",
            "execute_action": "execute_action",
            END: END
        }
    )
    
    # Add edge from process_image to classify_intent
    workflow.add_edge("process_image", "classify_intent")
    
    # Add conditional edges from classify_intent
    workflow.add_conditional_edges(
        "classify_intent",
        route_from_classify,
        {
            "check_consequences": "check_consequences",
            "execute_action": "execute_action",
            END: END
        }
    )
    
    # Add conditional edges from check_consequences
    workflow.add_conditional_edges(
        "check_consequences",
        route_from_consequences,
        {
            "get_confirmation": "get_confirmation",
            "execute_action": "execute_action"
        }
    )
    
    # Add edge from get_confirmation to END (wait for user response)
    workflow.add_edge("get_confirmation", END)
    
    # Add edge from execute_action to END
    workflow.add_edge("execute_action", END)
    
    # Compile and return
    agent_graph = workflow.compile()
    return agent_graph


# ============================================================================
# EXPORT
# ============================================================================

# Build and export the agent graph
agent_graph = build_agent_graph()

