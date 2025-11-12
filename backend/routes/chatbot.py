"""
Chatbot API routes
"""

from fastapi import APIRouter, HTTPException
from backend.models.schemas import ChatRequest, ChatResponse
from backend.services.chatbot_service import ChatbotService

router = APIRouter()
service = ChatbotService()


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat endpoint - sends messages to Groq API and returns response
    
    Request body:
    - messages: List of chat messages (conversation history)
    - temperature: Optional temperature for response (default: 0.7)
    - max_tokens: Optional max tokens (default: 500)
    
    Returns:
    - message: Assistant's response text
    - role: "assistant"
    """
    try:
        result = service.chat(
            messages=request.messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        return ChatResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

