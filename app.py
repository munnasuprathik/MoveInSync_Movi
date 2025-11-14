import base64
import logging
import os
import json
import re
from typing import Any, Literal, Optional, TypedDict, Annotated
from datetime import datetime

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, AIMessage
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from pydantic import BaseModel

# Import existing CRUD routers so the legacy API continues to function
from backend.routes import stops, paths, routes, vehicles, drivers, trips, deployments

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Loading environment variables from .env")
load_dotenv()

PROJECT_REF = os.environ.get("SUPABASE_PROJECT_REF")
ACCESS_TOKEN = os.environ.get("SUPABASE_ACCESS_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

if not PROJECT_REF or not ACCESS_TOKEN:
    raise RuntimeError("SUPABASE_PROJECT_REF and SUPABASE_ACCESS_TOKEN must be set.")
if not ANTHROPIC_API_KEY:
    raise RuntimeError("ANTHROPIC_API_KEY must be set.")

SUPABASE_URL = f"https://mcp.supabase.com/mcp?project_ref={PROJECT_REF}&features=database"
SUPABASE_HEADERS = {"Authorization": f"Bearer {ACCESS_TOKEN}"}

os.environ["ANTHROPIC_API_KEY"] = ANTHROPIC_API_KEY
logger.info("Claude model initialized")

# System Prompt for Movi
MOVI_SYSTEM_PROMPT = """You are Movi, an intelligent multimodal transport assistant for MoveInSync Shuttle platform.

# YOUR CORE UNDERSTANDING
You understand the transport operations hierarchy:
1. STATIC ASSETS (Layer 1): Stop → Path → Route
   - Stop: Physical locations (e.g., "Gavipuram", "Peenya")
   - Path: Ordered sequence of stops
   - Route: Path + specific time assignment

2. DYNAMIC OPERATIONS (Layer 2): Route → Deployment → Trip → Trip-Sheet
   - Vehicles: Transport vehicles with capacity
   - Drivers: Assigned to vehicles
   - DailyTrips: Daily trip instances from routes (table: daily_trips)
   - Deployments: Links vehicles and drivers to trips

# DATABASE SCHEMA KNOWLEDGE
- Table names: vehicles, drivers, stops, paths, routes, daily_trips, deployments
- All tables have soft delete: Use "WHERE deleted_at IS NULL" in all queries
- Foreign keys: routes.path_id → paths, daily_trips.route_id → routes, deployments link trip_id, vehicle_id, driver_id

# YOUR CRITICAL RESPONSIBILITIES

## 1. CONSEQUENCE AWARENESS
Before ANY destructive operation (DELETE, UPDATE, REMOVE), you MUST:
- Check for dependencies and active bookings using database queries
- Identify impact on trips, bookings, and trip-sheets
- Warn the user with specific details (booking percentages, affected trips)
- Ask for explicit confirmation before proceeding

## 2. DATABASE OPERATIONS - STRICT RULES

### FOR CREATE OPERATIONS:
1. Query the table schema if needed to identify required fields
2. Ask ONE question at a time for each required field
3. NEVER hallucinate or generate dummy data
4. Only after collecting ALL required data, ask for confirmation
5. Execute the INSERT operation

### FOR READ OPERATIONS:
- Execute queries directly using available database tools
- Always add "WHERE deleted_at IS NULL" to filter soft-deleted records
- Present data clearly and concisely

### FOR UPDATE/DELETE OPERATIONS:
- ALWAYS check consequences first using database queries
- For DELETE, use soft delete: UPDATE table SET deleted_at = CURRENT_TIMESTAMP
- For deactivate route: UPDATE routes SET status = 'deactivated'
- Present findings with specific numbers
- Wait for explicit confirmation
- Only then execute the operation

## 3. PAGE CONTEXT AWARENESS
Current page: {current_page}
- **busDashboard**: Focus on daily_trips, deployments, live status
- **manageRoute**: Focus on stops, paths, routes configuration

## 4. EXTRACTING INFORMATION
- Extract trip names like "Bulk - 00:01" from queries
- Extract entity names in quotes
- Use ILIKE for case-insensitive matching in queries

## 5. MULTIMODAL CAPABILITIES
- Analyze uploaded images to identify specific items
- Extract trip names, routes from visual indicators

# BEHAVIOR GUIDELINES
- Be concise and professional
- Never make assumptions or hallucinate data
- Always validate before executing operations
- Provide clear warnings for destructive actions
- Guide users step-by-step
- Use the database tools provided - query real data
- Remember: All queries must include "WHERE deleted_at IS NULL"

Remember: You are helping transport managers make critical decisions. Accuracy and safety are paramount."""


# Agent State Definition
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    current_page: str
    pending_action: Optional[dict]
    consequences: Optional[dict]
    user_confirmed: Optional[bool]
    collected_data: Optional[dict]
    image_data: Optional[str]
    conversation_history: list


# Request/Response Models
class AgentRequest(BaseModel):
    query: str
    current_page: str = "busDashboard"
    conversation_id: Optional[str] = None
    image_data: Optional[str] = None
    confirmation: Optional[bool] = None


class AgentResponse(BaseModel):
    response: str
    requires_confirmation: bool = False
    collected_fields: Optional[dict] = None
    rate_limit_warning: bool = False
    conversation_id: Optional[str] = None


class LegacyChatRequest(BaseModel):
    message: str
    current_page: str
    session_id: str


class LegacyChatResponse(BaseModel):
    response: str
    awaiting_confirmation: bool = False


class LegacyUploadResponse(LegacyChatResponse):
    pass


# Global session storage
conversation_sessions = {}

# Schema-based configuration
TABLE_NAME_MAPPING = {
    "vehicle": "vehicles",
    "driver": "drivers",
    "stop": "stops",
    "path": "paths",
    "route": "routes",
    "trip": "daily_trips",
    "daily_trips": "daily_trips",
    "deployment": "deployments"
}

TABLE_REQUIRED_FIELDS = {
    "vehicles": ["license_plate", "type", "capacity"],
    "drivers": ["name", "phone_number"],
    "stops": ["name", "latitude", "longitude"],
    "paths": ["path_name", "ordered_list_of_stop_ids"],
    "routes": ["path_id", "route_display_name", "shift_time", "direction", "start_point", "end_point"],
    "daily_trips": ["route_id", "display_name"],
    "deployments": ["trip_id", "vehicle_id", "driver_id"]
}

FIELD_DESCRIPTIONS = {
    "license_plate": "the vehicle's license plate number (e.g., KA-01-1234)",
    "type": "the vehicle type (Bus or Cab)",
    "capacity": "the seating capacity (number of seats)",
    "name": "the name",
    "phone_number": "the phone number (e.g., +91-9876543210)",
    "latitude": "the latitude coordinate (e.g., 12.9716)",
    "longitude": "the longitude coordinate (e.g., 77.5946)",
    "path_name": "the path name (e.g., Tech-Loop)",
    "ordered_list_of_stop_ids": "the stop names in order, separated by commas (e.g., Gavipuram, Temple, Peenya)",
    "route_display_name": "the route display name (e.g., Path2 - 19:45)",
    "shift_time": "the shift time (e.g., 19:45)",
    "direction": "the direction (Forward, Reverse, or Circular)",
    "start_point": "the starting point name",
    "end_point": "the ending point name",
    "path_id": "the path name",
    "trip_id": "the trip name",
    "vehicle_id": "the vehicle license plate",
    "driver_id": "the driver name",
    "display_name": "the trip display name (e.g., Bulk - 00:01)"
}


def _is_rate_limit_error(error_msg: str) -> bool:
    lowered = error_msg.lower()
    return "rate limit" in lowered or "429" in error_msg or "overloaded" in lowered


class MoviAgent:
    def __init__(self, session: ClientSession, tools: list):
        self.session = session
        self.mcp_tools = tools
        self.model = ChatAnthropic(
            model="claude-sonnet-4-5-20250929",
            temperature=0,
            max_tokens=8192
        )
        self.graph = self._build_graph()
        logger.info(f"MoviAgent initialized with {len(tools)} MCP tools")
        
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state graph for Movi"""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("agent_entry", self.agent_entry_node)
        workflow.add_node("process_multimodal", self.process_multimodal_node)
        workflow.add_node("check_consequences", self.check_consequences_node)
        workflow.add_node("collect_data", self.collect_data_node)
        workflow.add_node("get_confirmation", self.get_confirmation_node)
        workflow.add_node("execute_action", self.execute_action_node)
        workflow.add_node("final_response", self.final_response_node)
        
        # Set entry point
        workflow.set_entry_point("agent_entry")
        
        # Add conditional edges
        workflow.add_conditional_edges(
            "agent_entry",
            self.route_from_entry,
            {
                "multimodal": "process_multimodal",
                "collect_data": "collect_data",
                "check_consequences": "check_consequences",
                "execute": "execute_action",
                "respond": "final_response"
            }
        )
        
        workflow.add_conditional_edges(
            "process_multimodal",
            self.route_after_multimodal,
            {
                "check_consequences": "check_consequences",
                "respond": "final_response"
            }
        )
        
        workflow.add_edge("collect_data", "final_response")
        workflow.add_edge("check_consequences", "get_confirmation")
        workflow.add_edge("get_confirmation", "final_response")
        
        workflow.add_conditional_edges(
            "execute_action",
            self.route_after_execution,
            {
                "respond": "final_response",
                "error": "final_response"
            }
        )
        
        workflow.add_edge("final_response", END)
        
        return workflow.compile()
    
    def _extract_entity_info(self, query: str) -> dict:
        """Extract entity name and type from query"""
        query_lower = query.lower()
        
        # Detect entity type
        entity_type = None
        if any(word in query_lower for word in ["vehicle", "car", "bus", "cab"]):
            entity_type = "vehicle"
        elif "driver" in query_lower:
            entity_type = "driver"
        elif "trip" in query_lower:
            entity_type = "trip"
        elif "route" in query_lower:
            entity_type = "route"
        elif "stop" in query_lower:
            entity_type = "stop"
        elif "path" in query_lower:
            entity_type = "path"
        
        # Extract name from quotes or patterns
        name = None
        match = re.search(r"'([^']+)'|\"([^\"]+)\"|'([^']+)'", query)
        if match:
            name = match.group(1) or match.group(2) or match.group(3)
        else:
            # Look for trip pattern like "Bulk - 00:01"
            match = re.search(r"([A-Za-z0-9]+ - \d{2}:\d{2})", query)
            if match:
                name = match.group(1)
        
        return {"entity_type": entity_type, "entity_name": name}
    
    def _is_confirmation(self, text: str) -> bool:
        """Check if user is confirming"""
        text_lower = text.lower().strip()
        confirmations = ["yes", "y", "confirm", "proceed", "ok", "sure", "go ahead", "do it"]
        denials = ["no", "n", "cancel", "stop", "don't", "abort"]
        
        if any(word in text_lower for word in confirmations):
            return True
        if any(word in text_lower for word in denials):
            return False
        return None
    
    def _normalize_table_name(self, table_name: str) -> str:
        """Convert user input to actual table name"""
        if not table_name:
            return None
        normalized = table_name.lower().strip()
        return TABLE_NAME_MAPPING.get(normalized, normalized)
    
    def route_from_entry(self, state: AgentState) -> str:
        """Determine next node based on intent classification"""
        pending_action = state.get("pending_action") or {}
        intent = pending_action.get("intent")
        
        # Check for image input first
        if state.get("image_data") and not pending_action.get("multimodal_processed"):
            return "multimodal"
        
        # Check for confirmation response
        if pending_action.get("awaiting_confirmation") and state.get("user_confirmed") is not None:
            if state.get("user_confirmed"):
                return "execute"
            else:
                return "respond"
        
        # Check for data collection in progress
        collected_data = state.get("collected_data") or {}
        if intent == "create" and collected_data and not collected_data.get("complete"):
            return "collect_data"
        
        # New create operation
        if intent == "create" and not collected_data:
            return "collect_data"
        
        # Destructive operations need consequence check
        if intent in ["delete", "remove", "deactivate"] and not state.get("consequences"):
            return "check_consequences"
        
        # Execute after confirmation
        if intent == "execute" and state.get("user_confirmed"):
            return "execute"
        
        # Default: respond
        return "respond"
    
    def route_after_multimodal(self, state: AgentState) -> str:
        """Route after multimodal processing"""
        pending_action = state.get("pending_action") or {}
        if pending_action.get("intent") in ["delete", "remove"]:
            return "check_consequences"
        return "respond"
    
    def route_after_execution(self, state: AgentState) -> str:
        """Route after execution attempt"""
        if (state.get("pending_action") or {}).get("error"):
            return "error"
        return "respond"
    
    async def agent_entry_node(self, state: AgentState) -> AgentState:
        """Initial processing and intent classification"""
        messages = state["messages"]
        current_page = state.get("current_page", "busDashboard")
        last_message = messages[-1].content if messages and hasattr(messages[-1], 'content') else str(messages[-1]) if messages else ""
        
        # Check if this is a confirmation response
        confirmation = self._is_confirmation(last_message)
        if confirmation is not None and (state.get("pending_action") or {}).get("awaiting_confirmation"):
            state["user_confirmed"] = confirmation
            if not confirmation:
                state["pending_action"]["intent"] = "cancelled"
            return state
        
        # Check if continuing data collection
        collected_data = state.get("collected_data") or {}
        if collected_data and not collected_data.get("complete"):
            state["pending_action"] = state.get("pending_action") or {}
            state["pending_action"]["intent"] = "create"
            return state
        
        # Extract entity information
        entity_info = self._extract_entity_info(last_message)
        
        # Classify intent using LLM
        classification_prompt = f"""Analyze this user query and classify the intent.

User query: "{last_message}"
Current page: {current_page}

Classify as ONE of these intents:
- "read": User wants to VIEW/LIST/GET data
- "create": User wants to ADD/INSERT new data
- "update": User wants to MODIFY existing data
- "delete": User wants to DELETE/REMOVE data
- "deactivate": User wants to deactivate/disable
- "help": User needs guidance

Also identify:
- table_name: The database table involved (vehicles, drivers, stops, paths, routes, daily_trips, deployments)
- requires_data_collection: true ONLY if CREATE operation needs user input
- is_destructive: true if DELETE/REMOVE/DEACTIVATE operation
- extracted_entity_name: Any specific name/ID mentioned

Respond ONLY with valid JSON:
{{"intent": "...", "table_name": "...", "requires_data_collection": false, "is_destructive": false, "extracted_entity_name": null}}"""

        try:
            response = await self.model.ainvoke([{"role": "user", "content": classification_prompt}])
            
            content = response.content if hasattr(response, 'content') else str(response)
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            classification = json.loads(content)
            
            # Normalize table name
            table_name = self._normalize_table_name(classification.get("table_name"))
            
            state["pending_action"] = {
                "intent": classification.get("intent"),
                "table_name": table_name,
                "entity_type": entity_info.get("entity_type") or table_name,
                "entity_name": entity_info.get("entity_name") or classification.get("extracted_entity_name"),
                "requires_data_collection": classification.get("requires_data_collection", False),
                "is_destructive": classification.get("is_destructive", False),
                "original_query": last_message,
                "awaiting_confirmation": False
            }
            
            logger.info(f"Classified intent: {classification.get('intent')} for table: {table_name}")
            
        except Exception as e:
            logger.error(f"Intent classification error: {e}")
            state["pending_action"] = {
                "intent": "help",
                "error": str(e),
                "original_query": last_message
            }
        
        return state
    
    async def process_multimodal_node(self, state: AgentState) -> AgentState:
        """Process image inputs using Claude's vision"""
        image_data = state.get("image_data")
        messages = state.get("messages", [])
        query = messages[-1].content if messages and hasattr(messages[-1], 'content') else ""
        
        if not image_data:
            return state
        
        try:
            vision_prompt = """You are analyzing a screenshot of the MoveInSync transport dashboard.

Analyze this image and extract:
1. Which page is this? (busDashboard or manageRoute)
2. What specific trip/route/item is the user referring to?
3. Look for trip names like "Bulk - 00:01", route names, highlighted items
4. Extract relevant details like booking percentages, status

Respond ONLY with valid JSON:
{
  "page": "busDashboard or manageRoute",
  "identified_item": "exact trip/route name",
  "item_type": "trip, route, vehicle, or driver",
  "extracted_data": {"trip_name": "...", "booking_percentage": "...", "status": "..."}
}"""
            
            response = await self.model.ainvoke([
                HumanMessage(content=[
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": image_data
                        }
                    },
                    {
                        "type": "text",
                        "text": f"{vision_prompt}\n\nUser query: {query}"
                    }
                ])
            ])
            
            content = response.content if hasattr(response, 'content') else str(response)
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            
            vision_data = json.loads(content.strip())
            
            if vision_data.get("page"):
                state["current_page"] = vision_data["page"]
            
            if not state.get("pending_action"):
                state["pending_action"] = {}
            
            state["pending_action"]["entity_name"] = vision_data.get("identified_item")
            state["pending_action"]["item_type"] = vision_data.get("item_type")
            state["pending_action"]["extracted_data"] = vision_data.get("extracted_data", {})
            state["pending_action"]["multimodal_processed"] = True
            
            logger.info(f"Vision extracted: {vision_data.get('identified_item')} on {vision_data.get('page')}")
            
        except Exception as e:
            logger.error(f"Vision processing error: {e}")
            state["pending_action"] = state.get("pending_action") or {}
            state["pending_action"]["multimodal_error"] = str(e)
        
        return state
    
    async def check_consequences_node(self, state: AgentState) -> AgentState:
        """Check consequences of destructive operations with real database queries"""
        pending_action = state.get("pending_action") or {}
        intent = pending_action.get("intent")
        entity_name = pending_action.get("entity_name")
        entity_type = pending_action.get("entity_type")
        
        consequences = {
            "found": False,
            "severity": "none",
            "details": "",
            "affected_items": []
        }
        
        try:
            model_with_tools = self.model.bind_tools(self.mcp_tools)
            
            # Build consequence check query
            consequence_query = f"""Check the consequences of this operation:
Intent: {intent}
Entity: {entity_type} - {entity_name}
Query: {pending_action.get('original_query')}

Execute appropriate SQL queries to check:
1. Active bookings or usage (check booking_status_percentage, total_bookings in daily_trips)
2. Dependencies (trips using this vehicle/driver/route, routes using this path, paths using this stop)
3. Impact on trip-sheet generation

IMPORTANT: Add "WHERE deleted_at IS NULL" to all queries to filter soft-deleted records.

Example queries:
- For removing vehicle from trip: SELECT dt.booking_status_percentage, dt.total_bookings, dt.live_status FROM daily_trips dt WHERE dt.display_name ILIKE '%{entity_name}%' AND dt.deleted_at IS NULL
- For deleting stop: SELECT COUNT(*) FROM paths WHERE '{entity_name}' = ANY(ordered_list_of_stop_ids) AND deleted_at IS NULL
- For deleting vehicle: SELECT COUNT(*) FROM deployments WHERE vehicle_id = (SELECT vehicle_id FROM vehicles WHERE license_plate = '{entity_name}' AND deleted_at IS NULL) AND deleted_at IS NULL

Report specific numbers and percentages found."""

            system_prompt = MOVI_SYSTEM_PROMPT.format(current_page=state.get("current_page", "busDashboard"))
            
            response = await model_with_tools.ainvoke([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": consequence_query}
            ])
            
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            # Check if consequences were found
            response_lower = response_text.lower()
            has_bookings = any(word in response_lower for word in ["booking", "booked", "%", "percent"])
            has_dependencies = any(word in response_lower for word in ["path", "route", "trip", "depend", "affect", "using"])
            has_warnings = any(word in response_lower for word in ["warning", "will", "cancel", "break", "fail"])
            
            if has_bookings or has_dependencies or has_warnings:
                consequences["found"] = True
                consequences["severity"] = "high" if has_bookings else "medium"
                consequences["details"] = response_text
                logger.info(f"Consequences found: {consequences['severity']} severity")
            else:
                consequences["found"] = False
                consequences["details"] = "No significant consequences detected."
                logger.info("No significant consequences found")
            
            state["consequences"] = consequences
            
        except Exception as e:
            logger.error(f"Consequence check error: {e}")
            state["consequences"] = {
                "found": False,
                "error": str(e),
                "details": f"Unable to check consequences: {str(e)}"
            }
        
        return state
    
    async def collect_data_node(self, state: AgentState) -> AgentState:
        """Collect required data for CREATE operations step by step"""
        pending_action = state.get("pending_action") or {}
        collected_data = state.get("collected_data") or {}
        table_name = pending_action.get("table_name", "").lower()
        messages = state.get("messages", [])
        
        # Get required fields
        fields = TABLE_REQUIRED_FIELDS.get(table_name, [])
        
        if not fields:
            state["messages"] = messages + [AIMessage(content=f"I'm not sure what information is needed to create a {table_name}. Could you provide more details?")]
            return state
        
        if not collected_data:
            # Initialize data collection
            state["collected_data"] = {
                "table_name": table_name,
                "fields_required": fields,
                "fields_collected": {},
                "current_field_index": 0,
                "complete": False
            }
            
            # Ask for first field
            first_field = fields[0]
            field_desc = FIELD_DESCRIPTIONS.get(first_field, first_field.replace('_', ' '))
            
            intro_message = f"To add a new {table_name.rstrip('s')}, I need the following information. Let's start:\n\n**1. Please provide {field_desc}:**"
            
            state["messages"] = messages + [AIMessage(content=intro_message)]
        else:
            # Continue collecting
            current_index = collected_data.get("current_field_index", 0)
            last_message = messages[-1].content if messages and hasattr(messages[-1], 'content') else str(messages[-1]) if messages else ""
            
            # Store the answer
            if current_index < len(fields):
                current_field = fields[current_index]
                collected_data["fields_collected"][current_field] = last_message.strip()
                
                # Move to next field
                next_index = current_index + 1
                collected_data["current_field_index"] = next_index
                
                if next_index < len(fields):
                    next_field = fields[next_index]
                    field_desc = FIELD_DESCRIPTIONS.get(next_field, next_field.replace('_', ' '))
                    
                    next_message = f"**{next_index + 1}. Please provide {field_desc}:**"
                    state["messages"] = messages + [AIMessage(content=next_message)]
                else:
                    # All fields collected
                    collected_data["complete"] = True
                    
                    # Build summary
                    summary_lines = ["✅ Great! I have all the information needed:"]
                    for field, value in collected_data["fields_collected"].items():
                        field_display = field.replace('_', ' ').title()
                        summary_lines.append(f"   • {field_display}: **{value}**")
                    
                    summary_lines.append(f"\n**Shall I proceed to add this {table_name.rstrip('s')}?** (Yes/No)")
                    
                    summary_message = "\n".join(summary_lines)
                    state["messages"] = messages + [AIMessage(content=summary_message)]
                    
                    # Mark as awaiting confirmation
                    pending_action["awaiting_confirmation"] = True
                    state["pending_action"] = pending_action
            
            state["collected_data"] = collected_data
        
        return state
    
    async def get_confirmation_node(self, state: AgentState) -> AgentState:
        """Ask user for confirmation after consequence check"""
        consequences = state.get("consequences") or {}
        messages = state.get("messages", [])
        pending_action = state.get("pending_action") or {}
        
        if consequences.get("found"):
            severity = consequences.get("severity", "medium")
            severity_emoji = "🚨" if severity == "high" else "⚠️"
            
            warning_message = f"""{severity_emoji} **WARNING: Potential Consequences Detected**

{consequences.get('details', 'This operation may have consequences.')}

**Do you want to proceed with this operation?** (Yes/No)"""
            
            state["messages"] = messages + [AIMessage(content=warning_message)]
            pending_action["awaiting_confirmation"] = True
            state["pending_action"] = pending_action
        else:
            no_consequence_msg = f"✅ No significant consequences detected. This operation appears safe.\n\n**Proceed with the operation?** (Yes/No)"
            state["messages"] = messages + [AIMessage(content=no_consequence_msg)]
            pending_action["awaiting_confirmation"] = True
            state["pending_action"] = pending_action
        
        return state
    
    async def execute_action_node(self, state: AgentState) -> AgentState:
        """Execute the actual database operation"""
        pending_action = state.get("pending_action") or {}
        collected_data = state.get("collected_data") or {}
        intent = pending_action.get("intent")
        table_name = pending_action.get("table_name", "")
        entity_name = pending_action.get("entity_name")
        
        try:
            model_with_tools = self.model.bind_tools(self.mcp_tools)
            
            # Build execution prompt
            if intent == "create":
                fields_collected = collected_data.get("fields_collected", {})
                execution_prompt = f"""Execute this database INSERT operation:

Table: {table_name}
Data to insert: {json.dumps(fields_collected)}

Build and execute the appropriate INSERT query. For foreign keys:
- For paths: Convert stop names to stop_ids by querying stops table
- For routes: Convert path name to path_id by querying paths table
- For deployments: Convert vehicle license_plate to vehicle_id, driver name to driver_id, trip name to trip_id

Always add "AND deleted_at IS NULL" when looking up foreign keys.
Use RETURNING * to return the inserted record.

Execute the query and return the result."""

            elif intent in ["delete", "remove"]:
                execution_prompt = f"""Execute this SOFT DELETE operation:

Table: {table_name}
Entity to delete: {entity_name}

Use UPDATE to set deleted_at = CURRENT_TIMESTAMP instead of hard DELETE.
Example: UPDATE {table_name} SET deleted_at = CURRENT_TIMESTAMP WHERE [condition] AND deleted_at IS NULL

For deployments, remove by trip name.
For routes, use UPDATE to set status = 'deactivated' instead.

Execute and return the result."""

            else:
                execution_prompt = f"""Execute this database operation:
Intent: {intent}
Table: {table_name}
Entity: {entity_name}
Original query: {pending_action.get('original_query')}

Determine the appropriate SQL statement and execute it.
Remember to include "WHERE deleted_at IS NULL" for all queries."""
            
            # Execute with tools
            system_prompt = MOVI_SYSTEM_PROMPT.format(current_page=state.get("current_page", "busDashboard"))
            
            response = await model_with_tools.ainvoke([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": execution_prompt}
            ])
            
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            state["pending_action"]["result"] = response_text
            state["pending_action"]["success"] = True
            
            logger.info(f"Operation executed successfully: {intent} on {table_name}")
            
        except Exception as e:
            logger.error(f"Execution error: {e}")
            state["pending_action"]["error"] = str(e)
            state["pending_action"]["success"] = False
        
        return state
    
    async def final_response_node(self, state: AgentState) -> AgentState:
        """Generate final response to user"""
        pending_action = state.get("pending_action") or {}
        messages = state.get("messages", [])
        intent = pending_action.get("intent")
        
        # Check if user cancelled
        if intent == "cancelled":
            cancel_msg = "❌ Operation cancelled. Nothing was changed."
            state["messages"] = messages + [AIMessage(content=cancel_msg)]
            return state
        
        # Check if operation was executed
        if pending_action.get("success"):
            result_text = pending_action.get("result", "")
            success_msg = f"✅ **Operation completed successfully!**\n\n{result_text}"
            state["messages"] = messages + [AIMessage(content=success_msg)]
            return state
        
        # Check if there was an error
        if pending_action.get("error"):
            error_text = pending_action.get("error", "Unknown error")
            error_msg = f"❌ **Error occurred:**\n\n{error_text}\n\nPlease try again or contact support if the issue persists."
            state["messages"] = messages + [AIMessage(content=error_msg)]
            return state
        
        # For read operations or help requests
        if intent in ["read", "help", "respond"]:
            model_with_tools = self.model.bind_tools(self.mcp_tools)
            system_prompt = MOVI_SYSTEM_PROMPT.format(current_page=state.get("current_page", "busDashboard"))
            
            # Convert messages to proper format
            formatted_messages = [{"role": "system", "content": system_prompt}]
            for msg in messages:
                if isinstance(msg, HumanMessage):
                    formatted_messages.append({"role": "user", "content": msg.content})
                elif isinstance(msg, AIMessage):
                    formatted_messages.append({"role": "assistant", "content": msg.content})
                else:
                    # Handle dict format
                    formatted_messages.append(msg)
            
            try:
                response = await model_with_tools.ainvoke(formatted_messages)
                response_text = response.content if hasattr(response, 'content') else str(response)
                state["messages"] = messages + [AIMessage(content=response_text)]
            except Exception as e:
                logger.error(f"Final response error: {e}")
                error_msg = f"I encountered an error while processing your request: {str(e)}"
                state["messages"] = messages + [AIMessage(content=error_msg)]
        
        return state
    
    async def process(self, query: str, current_page: str, conversation_id: Optional[str] = None, 
                     image_data: Optional[str] = None) -> dict:
        """Process a query through the graph"""
        
        # Retrieve or create conversation state
        if conversation_id and conversation_id in conversation_sessions:
            state = conversation_sessions[conversation_id]
            state["messages"].append(HumanMessage(content=query))
            if image_data:
                state["image_data"] = image_data
        else:
            state = AgentState(
                messages=[HumanMessage(content=query)],
                current_page=current_page,
                pending_action=None,
                consequences=None,
                user_confirmed=None,
                collected_data=None,
                image_data=image_data,
                conversation_history=[]
            )
            conversation_id = f"conv_{datetime.now().timestamp()}"
        
        # Run the graph
        try:
            result = await self.graph.ainvoke(state)
            
            # Store state for next turn
            conversation_sessions[conversation_id] = result
            
            # Extract final response
            final_messages = result.get("messages", [])
            if final_messages:
                last_message = final_messages[-1]
                if isinstance(last_message, AIMessage):
                    final_response = last_message.content
                elif hasattr(last_message, 'content'):
                    final_response = last_message.content
                else:
                    final_response = str(last_message)
            else:
                final_response = "I'm sorry, I couldn't process that request."
            
            return {
                "response": final_response,
                "conversation_id": conversation_id,
                "requires_confirmation": result.get("pending_action", {}).get("awaiting_confirmation", False),
                "collected_fields": result.get("collected_data")
            }
            
        except Exception as e:
            logger.error(f"Graph execution error: {e}")
            return {
                "response": f"I encountered an error: {str(e)}",
                "conversation_id": conversation_id,
                "requires_confirmation": False,
                "collected_fields": None
            }


# FastAPI App
app = FastAPI(title="Movi - MoveInSync AI Assistant")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:5000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Re-register legacy CRUD routers so existing frontend requests keep working
app.include_router(stops.router, prefix="/api/stops", tags=["Stops"])
app.include_router(paths.router, prefix="/api/paths", tags=["Paths"])
app.include_router(routes.router, prefix="/api/routes", tags=["Routes"])
app.include_router(vehicles.router, prefix="/api/vehicles", tags=["Vehicles"])
app.include_router(drivers.router, prefix="/api/drivers", tags=["Drivers"])
app.include_router(trips.router, prefix="/api/trips", tags=["Trips"])
app.include_router(deployments.router, prefix="/api/deployments", tags=["Deployments"])


async def _run_agent_request(payload: AgentRequest) -> AgentResponse:
    logger.info(f"Received request: {payload.query[:100]}...")

    try:
        async with streamablehttp_client(SUPABASE_URL, headers=SUPABASE_HEADERS) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await load_mcp_tools(session)
                logger.info(f"Loaded {len(tools)} MCP tools")

                agent = MoviAgent(session, tools)
                result = await agent.process(
                    query=payload.query,
                    current_page=payload.current_page,
                    conversation_id=payload.conversation_id,
                    image_data=payload.image_data
                )

                response = AgentResponse(
                    response=result["response"],
                    requires_confirmation=result.get("requires_confirmation", False),
                    collected_fields=result.get("collected_fields"),
                    rate_limit_warning=False,
                    conversation_id=result.get("conversation_id")
                )
                return response

    except ExceptionGroup as eg:
        logger.error(f"TaskGroup error: {eg}")
        actual_error = eg.exceptions[0] if eg.exceptions else eg
        raise Exception(f"Agent processing error: {str(actual_error)}") from actual_error
    except Exception as e:
        logger.error(f"Agent request error: {e}")
        raise


@app.post("/agent", response_model=AgentResponse)
async def invoke_agent(payload: AgentRequest):
    """Main endpoint for Movi agent"""
    try:
        return await _run_agent_request(payload)
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Agent error: {error_msg}")

        if _is_rate_limit_error(error_msg):
            return AgentResponse(
                response="⏳ **Rate Limit Notice:** I'm experiencing high demand right now. Please wait a moment and try again.\n\nRate limits help ensure quality service for all users. Thank you for your patience!",
                rate_limit_warning=True,
                conversation_id=payload.conversation_id
            )

        raise HTTPException(status_code=500, detail=f"Agent error: {error_msg}")


@app.post("/api/chat", response_model=LegacyChatResponse)
async def legacy_chat_endpoint(payload: LegacyChatRequest):
    """Backward-compatible endpoint for the existing frontend chatbot."""
    agent_payload = AgentRequest(
        query=payload.message,
        current_page=payload.current_page,
        conversation_id=payload.session_id
    )

    try:
        agent_response = await _run_agent_request(agent_payload)
        return LegacyChatResponse(
            response=agent_response.response,
            awaiting_confirmation=agent_response.requires_confirmation
        )
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Legacy chat error: {error_msg}")

        if _is_rate_limit_error(error_msg):
            return LegacyChatResponse(
                response="⏳ Rate limit reached. Please wait a bit before sending the next message.",
                awaiting_confirmation=False
            )

        raise HTTPException(status_code=500, detail=f"Agent error: {error_msg}")


@app.post("/api/upload-image", response_model=LegacyUploadResponse)
async def legacy_upload_endpoint(
    file: UploadFile = File(...),
    message: str = Form(...),
    current_page: str = Form(...),
    session_id: str = Form(...)
):
    """Backward-compatible image upload endpoint for the frontend chatbot."""
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    raw_bytes = await file.read()
    image_data = base64.b64encode(raw_bytes).decode("utf-8")

    agent_payload = AgentRequest(
        query=message,
        current_page=current_page,
        conversation_id=session_id,
        image_data=image_data
    )

    try:
        agent_response = await _run_agent_request(agent_payload)
        return LegacyUploadResponse(
            response=agent_response.response,
            awaiting_confirmation=agent_response.requires_confirmation
        )
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Legacy upload error: {error_msg}")

        if _is_rate_limit_error(error_msg):
            return LegacyUploadResponse(
                response="⏳ Rate limit reached while processing the image. Please retry shortly.",
                awaiting_confirmation=False
            )

        raise HTTPException(status_code=500, detail=f"Agent error: {error_msg}")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "agent": "Movi", 
        "model": "Claude Sonnet 4.5",
        "version": "1.0.0"
    }


@app.post("/reset-conversation")
async def reset_conversation(conversation_id: str):
    """Reset a conversation session"""
    if conversation_id in conversation_sessions:
        del conversation_sessions[conversation_id]
        return {"status": "success", "message": f"Conversation {conversation_id} reset"}
    return {"status": "not_found", "message": "Conversation not found"}


@app.get("/active-conversations")
async def get_active_conversations():
    """Get count of active conversation sessions"""
    return {
        "active_sessions": len(conversation_sessions),
        "session_ids": list(conversation_sessions.keys())
    }