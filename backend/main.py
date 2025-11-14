"""
FastAPI application for Movi backend API with LangGraph agent integration
"""

import sys
from pathlib import Path

# Add project root to Python path (allows running from any directory)
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict
import base64
import logging

# Import LangGraph agent
from backend.agent import agent_graph, AgentState

# Import CRUD routers (keep existing functionality)
from backend.routes import stops, paths, routes, vehicles, drivers, trips, deployments

app = FastAPI(
    title="Movi API",
    description="Backend API for Movi transport management system with AI agent",
    version="2.0.0"
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")
logger = logging.getLogger(__name__)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5000", "*"],  # Allow frontend origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Store agent sessions in memory (use Redis in production for scalability)
# Session structure: {session_id: AgentState}
sessions: Dict[str, AgentState] = {}

# Include CRUD routers (keep all existing endpoints)
app.include_router(stops.router, prefix="/api/stops", tags=["Stops"])
app.include_router(paths.router, prefix="/api/paths", tags=["Paths"])
app.include_router(routes.router, prefix="/api/routes", tags=["Routes"])
app.include_router(vehicles.router, prefix="/api/vehicles", tags=["Vehicles"])
app.include_router(drivers.router, prefix="/api/drivers", tags=["Drivers"])
app.include_router(trips.router, prefix="/api/trips", tags=["Trips"])
app.include_router(deployments.router, prefix="/api/deployments", tags=["Deployments"])


# ============================================================================
# PYDANTIC MODELS FOR AGENT API
# ============================================================================

class ChatRequest(BaseModel):
    """Request model for text chat messages"""
    message: str
    current_page: str  # "busDashboard" or "manageRoute"
    session_id: str


class ChatResponse(BaseModel):
    """Response model for chat endpoints"""
    response: str
    awaiting_confirmation: bool


# ============================================================================
# AGENT ENDPOINTS
# ============================================================================

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Handle text chat messages through LangGraph agent.
    
    This endpoint processes user messages using the Movi AI agent which:
    - Understands user intent using Gemini with function calling
    - Executes database operations through tools
    - Checks for consequences before dangerous actions
    - Requests confirmation when needed
    
    Args:
        request: ChatRequest with message, current_page, and session_id
        
    Returns:
        ChatResponse with assistant response and confirmation status
    """
    try:
        logger.info("chat endpoint: session_id=%s page=%s message=%s",
                    request.session_id, request.current_page, request.message)
        # Validate current_page
        if request.current_page not in ["busDashboard", "manageRoute"]:
            raise HTTPException(
                status_code=400,
                detail="current_page must be either 'busDashboard' or 'manageRoute'"
            )
        
        # Get or create session state
        if request.session_id not in sessions:
            logger.info("chat endpoint: creating new session %s", request.session_id)
            sessions[request.session_id] = {
                "messages": [],
                "current_page": request.current_page,
                "pending_action": None,
                "consequences": None,
                "awaiting_confirmation": False,
                "image_data": None,
                "image_mime_type": None,
                "form_state": None,
                "session_id": request.session_id
            }
        
        # Get current state
        state = sessions[request.session_id]
        
        # Update with new message and current page
        state["current_page"] = request.current_page
        state["messages"].append({
            "role": "user",
            "content": request.message
        })
        
        # Invoke LangGraph agent
        result = agent_graph.invoke(state)
        logger.info("chat endpoint: agent invocation complete for session %s", request.session_id)
        
        # Update session with new state
        sessions[request.session_id] = result
        
        # Extract last assistant message
        assistant_messages = [
            msg for msg in result.get("messages", [])
            if msg.get("role") == "assistant"
        ]
        
        if assistant_messages:
            response_text = assistant_messages[-1].get("content", "I'm here to help!")
        else:
            response_text = "I'm here to help! What would you like to do?"
        
        response = ChatResponse(
            response=response_text,
            awaiting_confirmation=result.get("awaiting_confirmation", False)
        )
        logger.info("chat endpoint: response=%s awaiting_confirmation=%s",
                    response.response, response.awaiting_confirmation)
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("chat endpoint error: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Sorry, I encountered an error: {str(e)}"
        )


@app.post("/api/upload-image", response_model=ChatResponse)
async def upload_image(
    file: UploadFile = File(...),
    message: str = Form(...),
    current_page: str = Form(...),
    session_id: str = Form(...)
):
    """
    Handle image uploads with text instructions.
    
    This endpoint processes dashboard screenshots to extract trip information.
    The agent uses Gemini Vision to identify highlighted/circled trips in images.
    
    Args:
        file: Image file (screenshot of dashboard)
        message: User's text instruction about the image
        current_page: Current page context ("busDashboard" or "manageRoute")
        session_id: Session identifier for conversation continuity
        
    Returns:
        ChatResponse with processed response and confirmation status
    """
    try:
        logger.info("upload_image: session=%s page=%s filename=%s", session_id, current_page, file.filename)
        # Validate current_page
        if current_page not in ["busDashboard", "manageRoute"]:
            raise HTTPException(
                status_code=400,
                detail="current_page must be either 'busDashboard' or 'manageRoute'"
            )
        
        # Validate file type
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(
                status_code=400,
                detail="File must be an image"
            )
        
        # Read and encode image
        image_data = await file.read()
        base64_image = base64.b64encode(image_data).decode('utf-8')
        
        # Get or create session
        if session_id not in sessions:
            logger.info("upload_image: creating new session %s", session_id)
            sessions[session_id] = {
                "messages": [],
                "current_page": current_page,
                "pending_action": None,
                "consequences": None,
                "awaiting_confirmation": False,
                "image_data": None,
                "image_mime_type": None,
                "form_state": None,
                "session_id": session_id
            }
        
        # Get current state
        state = sessions[session_id]
        
        # Update state with image and message
        state["current_page"] = current_page
        state["image_data"] = base64_image
        state["image_mime_type"] = file.content_type or "image/png"
        state["messages"].append({
            "role": "user",
            "content": message
        })
        
        # Invoke agent (will process image in process_image_node)
        result = agent_graph.invoke(state)
        logger.info("upload_image: agent invocation complete session=%s", session_id)
        
        # Update session
        sessions[session_id] = result
        
        # Extract response
        assistant_messages = [
            msg for msg in result.get("messages", [])
            if msg.get("role") == "assistant"
        ]
        
        if assistant_messages:
            response_text = assistant_messages[-1].get("content", "Image processed!")
        else:
            response_text = "Image processed! How can I help you?"
        
        response = ChatResponse(
            response=response_text,
            awaiting_confirmation=result.get("awaiting_confirmation", False)
        )
        logger.info("upload_image: response=%s awaiting_confirmation=%s",
                    response.response, response.awaiting_confirmation)
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("upload_image error: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Sorry, I encountered an error processing the image: {str(e)}"
        )


@app.get("/api/session/{session_id}")
async def get_session(session_id: str):
    """
    Get current session state for debugging.
    
    This endpoint allows you to inspect the current state of an agent session,
    including conversation history, pending actions, and confirmation status.
    
    Args:
        session_id: Session identifier
        
    Returns:
        Current AgentState for the session
    """
    logger.info("get_session endpoint: session=%s", session_id)
    if session_id in sessions:
        return sessions[session_id]
    raise HTTPException(status_code=404, detail="Session not found")


@app.delete("/api/session/{session_id}")
async def delete_session(session_id: str):
    """
    Delete a session and clear its state.
    
    Args:
        session_id: Session identifier to delete
        
    Returns:
        Success message
    """
    logger.info("delete_session endpoint: session=%s", session_id)
    if session_id in sessions:
        del sessions[session_id]
        return {"message": f"Session {session_id} deleted successfully"}
    raise HTTPException(status_code=404, detail="Session not found")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Movi API",
        "version": "2.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

