"""
FastAPI routes for MCP Agent with state management.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Request
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
from backend.models.schemas import ChatRequest, ChatResponse, ChatMessage
from backend.mcp.langgraph_client import get_langgraph_client
from backend.mcp.tools.route_management_tools import ROUTE_MANAGEMENT_STATE
from backend.mcp.tools.bus_dashboard_tools import BUS_DASHBOARD_STATE
from typing import Optional, List
import json
import asyncio
import base64

router = APIRouter()

# Valid states
VALID_STATES = {
    "route_management": ROUTE_MANAGEMENT_STATE,
    "bus_dashboard": BUS_DASHBOARD_STATE
}


@router.post("/chat", response_model=ChatResponse)
async def chat_with_agent(
    request: Request,
    state: str = "route_management",
    image: Optional[UploadFile] = File(None)
):
    """
    Chat with MCP agent (non-streaming).
    
    Query params:
    - state: Current page state (route_management or bus_dashboard)
    
    Request body (JSON):
    - messages: List of chat messages
    """
    # Validate state
    if state not in VALID_STATES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid state. Must be one of: {list(VALID_STATES.keys())}"
        )
    
    normalized_state = VALID_STATES[state]
    
    # Parse request body (can be JSON or FormData)
    content_type = request.headers.get("content-type", "")
    
    if "application/json" in content_type:
        # JSON format
        body = await request.json()
        messages_data = body.get("messages", [])
    elif "multipart/form-data" in content_type:
        # FormData format
        form = await request.form()
        messages_str = form.get("messages")
        if messages_str:
            try:
                messages_data = json.loads(messages_str)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid messages format")
        else:
            raise HTTPException(status_code=400, detail="No messages provided")
    else:
        raise HTTPException(status_code=400, detail="Unsupported content type")
    
    if not messages_data:
        raise HTTPException(status_code=400, detail="No messages provided")
    
    # Convert to ChatRequest format
    chat_messages = [ChatMessage(**msg) if isinstance(msg, dict) else msg for msg in messages_data]
    last_message = chat_messages[-1]
    
    if last_message.role != "user":
        raise HTTPException(status_code=400, detail="Last message must be from user")
    
    try:
        client = get_langgraph_client()
        
        # Process image if provided (Part 4: Vision)
        image_base64 = None
        if image:
            image_bytes = await image.read()
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        # Chat with agent
        final_response = None
        error_occurred = False
        
        try:
            message_content = last_message.content if hasattr(last_message, "content") else str(last_message)
            async for event in client.chat(
                message_content,
                normalized_state,
                image_base64=image_base64
            ):
                if event.get("type") == "final_response":
                    final_response = event.get("content", "")
                    if final_response:
                        break
        except Exception as e:
            error_occurred = True
            import traceback
            error_trace = traceback.format_exc()
            print(f"Error in chat stream: {error_trace}")
            
            # Get detailed error message
            error_msg = str(e) if e else "Unknown error"
            if not error_msg or error_msg.strip() == "":
                error_msg = f"Error type: {type(e).__name__}"
            
            # Extract more details from traceback
            error_lines = error_trace.split('\n')
            if len(error_lines) > 1:
                # Get the actual error line (usually second to last)
                for line in reversed(error_lines):
                    if line.strip() and not line.strip().startswith('File'):
                        error_msg = f"{error_msg} - {line.strip()}"
                        break
            
            final_response = f"I encountered an error while processing your request: {error_msg}. Please check the backend logs for details."
        
        if not final_response or not final_response.strip():
            # Try to get a helpful default response
            final_response = "I received your message, but couldn't generate a response. This might be due to a configuration issue. Please check the backend logs for more details."
        
        return ChatResponse(message=final_response, role="assistant")
        
    except ValueError as e:
        # Handle configuration errors (e.g., missing API key)
        raise HTTPException(status_code=400, detail=f"Configuration error: {str(e)}")
    except Exception as e:
        # Log the full error for debugging
        import traceback
        error_trace = traceback.format_exc()
        print(f"MCP Agent Error: {error_trace}")  # Log to console for debugging
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")


@router.post("/chat/stream")
async def chat_with_agent_stream(
    request: ChatRequest,
    state: str = "route_management",
    image: Optional[UploadFile] = File(None)
):
    """
    Chat with MCP agent (streaming).
    
    Query params:
    - state: Current page state (route_management or bus_dashboard)
    
    Request body:
    - messages: List of chat messages
    """
    # Validate state
    if state not in VALID_STATES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid state. Must be one of: {list(VALID_STATES.keys())}"
        )
    
    normalized_state = VALID_STATES[state]
    
    # Get last user message
    if not request.messages:
        raise HTTPException(status_code=400, detail="No messages provided")
    
    last_message = request.messages[-1]
    if last_message.role != "user":
        raise HTTPException(status_code=400, detail="Last message must be from user")
    
    async def event_generator():
        """Generate SSE events for streaming"""
        try:
            client = get_langgraph_client()
            
            # Process image if provided (Part 4: Vision)
            image_base64 = None
            if image:
                image_bytes = await image.read()
                image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            
            async for event in client.chat(
                last_message.content,
                normalized_state,
                image_base64=image_base64
            ):
                yield {
                    "event": "message",
                    "data": json.dumps(event)
                }
            
            yield {
                "event": "done",
                "data": json.dumps({"type": "complete"})
            }
            
        except ValueError as e:
            # Handle configuration errors
            yield {
                "event": "error",
                "data": json.dumps({"error": f"Configuration error: {str(e)}"})
            }
        except Exception as e:
            # Log full error for debugging
            import traceback
            error_trace = traceback.format_exc()
            print(f"MCP Agent Streaming Error: {error_trace}")  # Log to console
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)})
            }
    
    return EventSourceResponse(event_generator())


@router.get("/tools")
async def list_tools(state: str = None):
    """
    List available MCP tools, optionally filtered by state.
    
    Query params:
    - state: Optional state filter (route_management or bus_dashboard)
    """
    from backend.mcp.server import mcp_server
    
    normalized_state = None
    if state:
        if state not in VALID_STATES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid state. Must be one of: {list(VALID_STATES.keys())}"
            )
        normalized_state = VALID_STATES[state]
    
    tools = await mcp_server.list_tools(normalized_state)
    return {"tools": tools, "count": len(tools)}

