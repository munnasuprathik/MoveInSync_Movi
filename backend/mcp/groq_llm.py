"""
Simple Groq LLM wrapper for LangGraph compatibility.
Uses Groq's OpenAI-compatible API directly.
"""

from typing import List, Optional, Any, Dict
from langchain_core.language_models import BaseChatModel
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, SystemMessage
import httpx
import os


class GroqLLM(BaseChatModel):
    """Groq LLM wrapper compatible with LangChain/LangGraph"""
    
    model_name: str = "llama-3.1-8b-instant"  # Updated: llama-3.1-70b-versatile was decommissioned
    groq_api_key: str
    temperature: float = 0.7
    base_url: str = "https://api.groq.com/openai/v1"
    _bound_tools: Optional[List[Any]] = None
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.groq_api_key:
            self.groq_api_key = os.getenv("GROQ_API_KEY")
        if not self.groq_api_key:
            raise ValueError("GROQ_API_KEY is required")
        self._bound_tools = kwargs.get("_bound_tools", None)
    
    @property
    def _llm_type(self) -> str:
        return "groq"
    
    def bind_tools(self, tools: List[Any], **kwargs: Any) -> "GroqLLM":
        """
        Bind tools to the LLM for function calling.
        Returns a new instance with tools bound.
        """
        # Create a new instance with tools
        bound_llm = GroqLLM(
            model_name=self.model_name,
            groq_api_key=self.groq_api_key,
            temperature=self.temperature,
            base_url=self.base_url
        )
        bound_llm._bound_tools = tools
        return bound_llm
    
    def _convert_tools_to_groq_format(self, tools: List[Any]) -> List[Dict[str, Any]]:
        """Convert LangChain tools to Groq function calling format"""
        groq_tools = []
        for tool in tools:
            if hasattr(tool, "name") and hasattr(tool, "description"):
                # LangChain Tool object
                tool_dict = {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description or f"Tool: {tool.name}",
                        "parameters": {}
                    }
                }
                # Try to get input schema from stored _input_schema attribute first
                if hasattr(tool, "_input_schema") and tool._input_schema:
                    tool_dict["function"]["parameters"] = tool._input_schema
                elif hasattr(tool, "args_schema"):
                    schema = tool.args_schema
                    if schema:
                        tool_dict["function"]["parameters"] = schema.schema() if hasattr(schema, "schema") else {}
                elif hasattr(tool, "args") and tool.args:
                    tool_dict["function"]["parameters"] = tool.args.schema() if hasattr(tool.args, "schema") else {}
                groq_tools.append(tool_dict)
            elif isinstance(tool, dict):
                # Already in dict format
                groq_tools.append(tool)
        return groq_tools
    
    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Generate chat response from Groq API"""
        # Convert messages to Groq format
        groq_messages = []
        for msg in messages:
            if isinstance(msg, SystemMessage):
                role = "system"
            elif isinstance(msg, AIMessage):
                role = "assistant"
                # Handle tool calls in AIMessage
                msg_dict = {"role": role}
                if hasattr(msg, "content") and msg.content:
                    msg_dict["content"] = str(msg.content)
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    msg_dict["tool_calls"] = [
                        {
                            "id": tc.get("id", f"call_{i}"),
                            "type": "function",
                            "function": {
                                "name": tc.get("name", ""),
                                "arguments": str(tc.get("args", {}))
                            }
                        }
                        for i, tc in enumerate(msg.tool_calls)
                    ]
                groq_messages.append(msg_dict)
                continue
            else:  # HumanMessage or other
                role = "user"
            
            content = msg.content if hasattr(msg, "content") else str(msg)
            # Skip empty messages
            if not content or not content.strip():
                continue
            groq_messages.append({"role": role, "content": str(content)})
        
        if not groq_messages:
            raise ValueError("No valid messages provided")
        
        # Prepare request payload with valid parameters only
        payload = {
            "model": self.model_name,
            "messages": groq_messages,
            "temperature": self.temperature,
        }
        
        # Add tools if bound
        if self._bound_tools:
            groq_tools = self._convert_tools_to_groq_format(self._bound_tools)
            if groq_tools:
                payload["tools"] = groq_tools
                payload["tool_choice"] = "auto"  # Let model decide when to use tools
        
        # Add max_tokens if provided, ensure it's within limits (max 8192 for llama-3.1-8b-instant)
        max_tokens = kwargs.get("max_tokens", 1024)
        payload["max_tokens"] = min(max_tokens, 8192)
        
        # Add stop sequences if provided
        if stop:
            payload["stop"] = stop
        
        # Call Groq API
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.groq_api_key}"
                    },
                    json=payload
                )
                
                # Better error handling
                if response.status_code != 200:
                    error_detail = "Unknown error"
                    try:
                        error_data = response.json()
                        error_detail = error_data.get("error", {}).get("message", str(error_data))
                    except:
                        error_detail = response.text
                    
                    raise Exception(f"Groq API error {response.status_code}: {error_detail}")
                
                data = response.json()
                
                # Extract response
                if not data.get("choices") or len(data["choices"]) == 0:
                    raise Exception("No response from Groq API")
                
                choice = data["choices"][0]
                message_data = choice["message"]
                content = message_data.get("content", "")
                
                # Handle tool calls
                tool_calls = []
                if "tool_calls" in message_data:
                    for tc in message_data["tool_calls"]:
                        tool_calls.append({
                            "id": tc.get("id", ""),
                            "name": tc.get("function", {}).get("name", ""),
                            "args": self._parse_tool_arguments(tc.get("function", {}).get("arguments", "{}"))
                        })
                
                # Create AIMessage with tool calls if present
                if tool_calls:
                    message = AIMessage(content=content or "", tool_calls=tool_calls)
                else:
                    message = AIMessage(content=content)
                
                return ChatResult(generations=[ChatGeneration(message=message)])
                
        except httpx.HTTPStatusError as e:
            error_detail = "Unknown error"
            try:
                error_data = e.response.json()
                error_detail = error_data.get("error", {}).get("message", str(error_data))
            except:
                error_detail = e.response.text
            raise Exception(f"Groq API error {e.response.status_code}: {error_detail}")
        except Exception as e:
            raise Exception(f"Groq API request failed: {str(e)}")
    
    def _parse_tool_arguments(self, arguments: str) -> Dict[str, Any]:
        """Parse tool arguments JSON string"""
        import json
        try:
            return json.loads(arguments)
        except:
            return {}
    
    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Async generate chat response from Groq API"""
        # Convert messages to Groq format
        groq_messages = []
        for msg in messages:
            if isinstance(msg, SystemMessage):
                role = "system"
            elif isinstance(msg, AIMessage):
                role = "assistant"
                # Handle tool calls in AIMessage
                msg_dict = {"role": role}
                if hasattr(msg, "content") and msg.content:
                    msg_dict["content"] = str(msg.content)
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    msg_dict["tool_calls"] = [
                        {
                            "id": tc.get("id", f"call_{i}"),
                            "type": "function",
                            "function": {
                                "name": tc.get("name", ""),
                                "arguments": str(tc.get("args", {}))
                            }
                        }
                        for i, tc in enumerate(msg.tool_calls)
                    ]
                groq_messages.append(msg_dict)
                continue
            else:  # HumanMessage or other
                role = "user"
            
            content = msg.content if hasattr(msg, "content") else str(msg)
            # Skip empty messages
            if not content or not content.strip():
                continue
            groq_messages.append({"role": role, "content": str(content)})
        
        if not groq_messages:
            raise ValueError("No valid messages provided")
        
        # Prepare request payload with valid parameters only
        payload = {
            "model": self.model_name,
            "messages": groq_messages,
            "temperature": self.temperature,
        }
        
        # Add tools if bound
        if self._bound_tools:
            groq_tools = self._convert_tools_to_groq_format(self._bound_tools)
            if groq_tools:
                payload["tools"] = groq_tools
                payload["tool_choice"] = "auto"  # Let model decide when to use tools
        
        # Add max_tokens if provided, ensure it's within limits (max 8192 for llama-3.1-8b-instant)
        max_tokens = kwargs.get("max_tokens", 1024)
        payload["max_tokens"] = min(max_tokens, 8192)
        
        # Add stop sequences if provided
        if stop:
            payload["stop"] = stop
        
        # Call Groq API async
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.groq_api_key}"
                    },
                    json=payload
                )
                
                # Better error handling
                if response.status_code != 200:
                    error_detail = "Unknown error"
                    try:
                        error_data = response.json()
                        error_detail = error_data.get("error", {}).get("message", str(error_data))
                    except:
                        error_detail = response.text
                    
                    raise Exception(f"Groq API error {response.status_code}: {error_detail}")
                
                data = response.json()
                
                # Extract response
                if not data.get("choices") or len(data["choices"]) == 0:
                    raise Exception("No response from Groq API")
                
                choice = data["choices"][0]
                message_data = choice["message"]
                content = message_data.get("content", "")
                
                # Handle tool calls
                tool_calls = []
                if "tool_calls" in message_data:
                    for tc in message_data["tool_calls"]:
                        tool_calls.append({
                            "id": tc.get("id", ""),
                            "name": tc.get("function", {}).get("name", ""),
                            "args": self._parse_tool_arguments(tc.get("function", {}).get("arguments", "{}"))
                        })
                
                # Create AIMessage with tool calls if present
                if tool_calls:
                    message = AIMessage(content=content or "", tool_calls=tool_calls)
                else:
                    message = AIMessage(content=content)
                
                return ChatResult(generations=[ChatGeneration(message=message)])
                
        except httpx.HTTPStatusError as e:
            error_detail = "Unknown error"
            try:
                error_data = e.response.json()
                error_detail = error_data.get("error", {}).get("message", str(error_data))
            except:
                error_detail = e.response.text
            raise Exception(f"Groq API error {e.response.status_code}: {error_detail}")
        except Exception as e:
            raise Exception(f"Groq API request failed: {str(e)}")

