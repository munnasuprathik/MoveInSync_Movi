"""
Service layer for chatbot operations
"""

import os
from typing import List, Dict, Any, Optional
import httpx
from backend.models.schemas import ChatMessage


class ChatbotService:
    """Service for chatbot business logic and Groq API integration"""
    
    def __init__(self):
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.groq_api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "llama-3.1-8b-instant"  # Updated: llama-3.1-70b-versatile was decommissioned
        
        if not self.groq_api_key:
            raise ValueError("GROQ_API_KEY environment variable is not set")
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for the chatbot"""
        return """You are a helpful assistant for a transport management system. 
Help users with questions about trips, routes, vehicles, drivers, and deployments. 
Be concise and helpful. When asked about specific data, inform them that you can help 
with general questions but they should check the dashboard for real-time data."""
    
    def chat(self, messages: List[ChatMessage], temperature: float = 0.7, max_tokens: int = 500) -> Dict[str, Any]:
        """
        Send chat messages to Groq API and get response
        
        Args:
            messages: List of chat messages (conversation history)
            temperature: Temperature for response generation (0.0-1.0)
            max_tokens: Maximum tokens in response
            
        Returns:
            Dictionary with assistant's response message
        """
        # Prepare messages for Groq API
        groq_messages = [
            {
                "role": "system",
                "content": self.get_system_prompt()
            }
        ]
        
        # Add conversation history
        for msg in messages:
            groq_messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # Call Groq API
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    self.groq_api_url,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.groq_api_key}"
                    },
                    json={
                        "model": self.model,
                        "messages": groq_messages,
                        "temperature": temperature,
                        "max_tokens": min(max_tokens, 8192)  # Ensure max_tokens doesn't exceed 8192 for llama-3.1-8b-instant
                    }
                )
                
                response.raise_for_status()
                data = response.json()
                
                # Extract assistant's message
                assistant_message = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                
                if not assistant_message:
                    assistant_message = "Sorry, I could not generate a response."
                
                return {
                    "message": assistant_message,
                    "role": "assistant"
                }
                
        except httpx.HTTPStatusError as e:
            # Get detailed error message from response
            error_detail = "Unknown error"
            try:
                error_data = e.response.json()
                error_detail = error_data.get("error", {}).get("message", str(error_data))
            except:
                error_detail = e.response.text or f"HTTP {e.response.status_code}"
            
            if e.response.status_code == 400:
                error_msg = f"Bad request: {error_detail}. Please check your request parameters."
            elif e.response.status_code == 401:
                error_msg = "Invalid API key. Please check GROQ_API_KEY."
            elif e.response.status_code == 429:
                error_msg = "Rate limit exceeded. Please try again later."
            else:
                error_msg = f"Groq API error {e.response.status_code}: {error_detail}"
            raise Exception(error_msg)
            
        except httpx.RequestError as e:
            raise Exception(f"Failed to connect to Groq API: {str(e)}")
            
        except Exception as e:
            raise Exception(f"Chat error: {str(e)}")

