"""
LangGraph MCP Client for Movi transport management system.
Uses async streamable HTTP client to interact with MCP server.
"""

import json
from typing import Dict, Any, List, Optional, AsyncIterator
from langchain_core.tools import Tool as LangChainTool
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from backend.mcp.server import mcp_server
from backend.mcp.tools.route_management_tools import ROUTE_MANAGEMENT_STATE
from backend.mcp.tools.bus_dashboard_tools import BUS_DASHBOARD_STATE
from backend.mcp.consequence_checker import ConsequenceChecker
from backend.mcp.vision_tool import VisionTool


class LangGraphMCPClient:
    """
    LangGraph-based MCP client that uses async streamable HTTP.
    Integrates MCP tools with LangGraph agent.
    """
    
    def __init__(self, groq_api_key: Optional[str] = None):
        """
        Initialize LangGraph MCP client.
        
        Args:
            groq_api_key: Groq API key for LLM (optional, can be set via env)
        """
        import os
        try:
            self.groq_api_key = groq_api_key or os.getenv("GROQ_API_KEY")
            if not self.groq_api_key:
                raise ValueError("GROQ_API_KEY is required")
            
            # Use custom GroqLLM wrapper (LangGraph with Groq)
            from backend.mcp.groq_llm import GroqLLM
            self.llm = GroqLLM(
                model_name="llama-3.1-8b-instant",  # Updated: llama-3.1-70b-versatile was decommissioned
                temperature=0.7,
                groq_api_key=self.groq_api_key
            )
            self.memory = MemorySaver()
            self.graph = None
            self.consequence_checker = ConsequenceChecker()
            self.vision_tool = VisionTool()
            self._build_graph()
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"Error initializing LangGraphMCPClient: {error_trace}")
            raise ValueError(f"Failed to initialize LangGraph client: {str(e) if e else 'Unknown error'}")
    
    def _create_langchain_tools(self, state: str) -> List[LangChainTool]:
        """Create LangChain tools from MCP tools for a specific state"""
        tools = []
        try:
            from backend.mcp.server import mcp_server
            mcp_tools = mcp_server.get_tools_for_state(state)
            
            if not mcp_tools:
                print(f"Warning: No tools found for state: {state}")
                return tools
            
            for mcp_tool in mcp_tools:
                try:
                    tool_name = mcp_tool.get("name", "")
                    if not tool_name:
                        print(f"Warning: Tool missing name: {mcp_tool}")
                        continue
                    
                    # Capture tool_name and inputSchema in closure
                    captured_tool_name = tool_name
                    captured_input_schema = mcp_tool.get("inputSchema", {})
                    
                    async def tool_func(**kwargs):
                        """Dynamic tool function"""
                        result = await mcp_server.call_tool(captured_tool_name, kwargs, state)
                        # Extract text from results
                        texts = [r.get("text", str(r)) for r in result]
                        return "\n".join(texts)
                    
                    # Create LangChain tool with input schema stored as attribute
                    langchain_tool = LangChainTool(
                        name=tool_name,
                        description=mcp_tool.get("description", f"Tool: {tool_name}"),
                        func=tool_func
                    )
                    # Store inputSchema as attribute for Groq conversion
                    langchain_tool._input_schema = captured_input_schema
                    tools.append(langchain_tool)
                except Exception as e:
                    print(f"Error creating tool {mcp_tool.get('name', 'unknown')}: {e}")
                    continue
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"Error creating LangChain tools: {error_trace}")
            # Return empty list rather than failing completely
            return []
        
        return tools
    
    def _build_graph(self):
        """Build LangGraph state graph with consequence checking (Part 3)"""
        # Define state
        from typing import TypedDict, Annotated
        from operator import add
        
        class AgentState(TypedDict):
            messages: Annotated[List, add]
            state: str  # route_management or bus_dashboard
            pending_action: Optional[Dict[str, Any]]  # Action waiting for confirmation
            consequences: Optional[Dict[str, Any]]  # Consequence check results
            image_data: Optional[str]  # Base64 image data for vision processing
        
        # Create graph
        graph = StateGraph(AgentState)
        
        # Add nodes
        graph.add_node("agent", self._agent_node)
        graph.add_node("tools", self._tools_node)
        graph.add_node("check_consequences", self._check_consequences_node)  # Part 3: Tribal Knowledge
        graph.add_node("get_confirmation", self._get_confirmation_node)  # Part 3: Confirmation flow
        graph.add_node("process_image", self._process_image_node)  # Part 4: Vision processing
        
        # Set entry point
        graph.set_entry_point("agent")
        
        # Add conditional edges from agent
        graph.add_conditional_edges(
            "agent",
            self._route_after_agent,
            {
                "tools": "tools",
                "check_consequences": "check_consequences",
                "process_image": "process_image",
                "end": END
            }
        )
        
        # Tools -> Check consequences or back to agent
        graph.add_conditional_edges(
            "tools",
            self._route_after_tools,
            {
                "check_consequences": "check_consequences",
                "agent": "agent",
                "end": END
            }
        )
        
        # Check consequences -> Get confirmation or execute
        graph.add_conditional_edges(
            "check_consequences",
            self._route_after_consequences,
            {
                "get_confirmation": "get_confirmation",
                "execute": "tools",  # Execute the action
                "agent": "agent"
            }
        )
        
        # Get confirmation -> Execute or cancel
        graph.add_conditional_edges(
            "get_confirmation",
            self._route_after_confirmation,
            {
                "execute": "tools",
                "cancel": "agent",
                "agent": "agent"
            }
        )
        
        # Process image -> Agent (with extracted info)
        graph.add_edge("process_image", "agent")
        
        # Compile with memory
        self.graph = graph.compile(checkpointer=self.memory)
    
    async def _agent_node(self, state: Dict[str, Any]):
        """Agent node that processes messages"""
        messages = state.get("messages", [])
        current_state = state.get("state", "route_management")
        
        # Get tools for current state
        tools = self._create_langchain_tools(current_state)
        
        # Bind tools to LLM
        llm_with_tools = self.llm.bind_tools(tools)
        
        # Get system prompt with state filtering (Layer 5.1)
        system_prompt = self._get_system_prompt(current_state, tools)
        
        # Convert messages to proper format for LLM
        from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
        
        formatted_messages = [SystemMessage(content=system_prompt)]
        for msg in messages:
            if isinstance(msg, dict):
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role == "user":
                    formatted_messages.append(HumanMessage(content=content))
                elif role == "assistant":
                    formatted_messages.append(AIMessage(content=content))
            elif isinstance(msg, (HumanMessage, AIMessage, SystemMessage)):
                formatted_messages.append(msg)
            else:
                # Try to extract content
                if hasattr(msg, "content"):
                    formatted_messages.append(HumanMessage(content=str(msg.content)))
                else:
                    formatted_messages.append(HumanMessage(content=str(msg)))
        
        # Get response from LLM
        try:
            response = await llm_with_tools.ainvoke(formatted_messages)
            
            # Ensure response has content
            if not hasattr(response, "content") or not response.content:
                # Create a default response if LLM didn't generate one
                from langchain_core.messages import AIMessage
                response = AIMessage(content="I understand your request. How can I help you further?")
            
            return {"messages": [response]}
        except Exception as e:
            # If LLM call fails, return an error message
            import traceback
            error_trace = traceback.format_exc()
            print(f"LLM invocation error: {error_trace}")
            
            # Get detailed error message
            error_msg = str(e) if e else "Unknown error"
            if not error_msg or error_msg.strip() == "":
                error_msg = f"Error type: {type(e).__name__}"
            
            from langchain_core.messages import AIMessage
            error_message = AIMessage(content=f"I encountered an error while calling the LLM: {error_msg}. Please check the backend logs for details.")
            return {"messages": [error_message]}
    
    def _get_system_prompt(self, state: str, tools: List[LangChainTool]) -> str:
        """
        Get system prompt with state-based tool filtering (Layer 5.1).
        Tells LLM which tools to use based on state.
        """
        tool_names = [tool.name for tool in tools]
        
        if state == ROUTE_MANAGEMENT_STATE:
            return f"""You are a helpful assistant for route management in a transport system.
You can help users manage stops, paths, and routes.

Available tools for route management: {', '.join(tool_names)}

IMPORTANT: Only use tools from the list above. Do not use any tools related to vehicles, drivers, trips, or deployments.
Focus on stops, paths, and routes operations only.

When the user asks about route management, use the appropriate tools to help them."""
        
        elif state == BUS_DASHBOARD_STATE:
            return f"""You are a helpful assistant for bus dashboard operations in a transport system.
You can help users manage vehicles, drivers, trips, and deployments.

Available tools for bus dashboard: {', '.join(tool_names)}

IMPORTANT: Only use tools from the list above. Do not use any tools related to stops, paths, or routes.
Focus on vehicles, drivers, trips, and deployments operations only.

When the user asks about bus dashboard operations, use the appropriate tools to help them."""
        
        else:
            return f"You are a helpful assistant. Available tools: {', '.join(tool_names)}"
    
    async def _tools_node(self, state: Dict[str, Any]):
        """Tools node that executes tool calls"""
        messages = state.get("messages", [])
        current_state = state.get("state", "route_management")
        last_message = messages[-1]
        
        # Get tool calls from last message
        tool_calls = getattr(last_message, "tool_calls", [])
        
        if not tool_calls:
            return {"messages": []}
        
        # Execute tools
        tool_results = []
        for tool_call in tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call.get("args", {})
            
            # Execute tool via MCP server
            result = await mcp_server.call_tool(tool_name, tool_args, current_state)
            tool_results.append({
                "tool_call_id": tool_call.get("id", ""),
                "content": "\n".join([r.get("text", str(r)) for r in result])
            })
        
        return {"messages": tool_results}
    
    def _route_after_agent(self, state: Dict[str, Any]) -> str:
        """Route after agent node - check for image, tool calls, or end"""
        messages = state.get("messages", [])
        last_message = messages[-1]
        image_data = state.get("image_data")
        
        # Check for image data (Part 4: Vision)
        if image_data:
            return "process_image"
        
        # Check if there are tool calls
        tool_calls = getattr(last_message, "tool_calls", [])
        if tool_calls:
            # Check if any tool call requires consequence checking
            for tool_call in tool_calls:
                tool_name = tool_call.get("name", "")
                if self._requires_consequence_check(tool_name, tool_call.get("args", {})):
                    return "check_consequences"
            return "tools"
        
        return "end"
    
    def _requires_consequence_check(self, tool_name: str, tool_args: Dict[str, Any]) -> bool:
        """Check if a tool call requires consequence checking"""
        # Tools that require consequence checking
        consequence_tools = [
            "delete_deployment",  # Removing vehicle/driver from trip
            "delete_trip",  # Deleting a trip
            "delete_route",  # Deleting a route
            "delete_path"  # Deleting a path
        ]
        return tool_name in consequence_tools
    
    async def _check_consequences_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check consequences node (Part 3: Tribal Knowledge).
        Queries DB to find consequences before executing actions.
        """
        messages = state.get("messages", [])
        last_message = messages[-1]
        pending_action = state.get("pending_action", {})
        
        # Get the tool call that triggered this
        tool_calls = getattr(last_message, "tool_calls", [])
        if not tool_calls:
            return {"messages": [], "consequences": None}
        
        tool_call = tool_calls[0]  # Check first tool call
        tool_name = tool_call.get("name", "")
        tool_args = tool_call.get("args", {})
        
        # Store pending action
        pending_action = {
            "tool_name": tool_name,
            "tool_args": tool_args,
            "tool_call_id": tool_call.get("id", "")
        }
        
        # Check consequences based on tool
        consequences = None
        
        if tool_name == "delete_deployment":
            # Check deployment removal consequences
            trip_id = tool_args.get("trip_id")
            deployment_id = tool_args.get("deployment_id")
            if trip_id:
                consequences = self.consequence_checker.check_deployment_removal_consequences(
                    trip_id, deployment_id
                )
        
        elif tool_name == "delete_trip":
            trip_id = tool_args.get("trip_id")
            if trip_id:
                consequences = self.consequence_checker.check_trip_deletion_consequences(trip_id)
        
        elif tool_name == "delete_route":
            route_id = tool_args.get("route_id")
            if route_id:
                consequences = self.consequence_checker.check_route_deletion_consequences(route_id)
        
        elif tool_name == "delete_path":
            path_id = tool_args.get("path_id")
            if path_id:
                consequences = self.consequence_checker.check_path_deletion_consequences(path_id)
        
        return {
            "messages": [],
            "pending_action": pending_action,
            "consequences": consequences
        }
    
    def _route_after_consequences(self, state: Dict[str, Any]) -> str:
        """Route after checking consequences"""
        consequences = state.get("consequences", {})
        
        if consequences and consequences.get("has_consequences"):
            return "get_confirmation"
        else:
            # No consequences, execute directly
            return "execute"
    
    async def _get_confirmation_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get confirmation node (Part 3: Tribal Knowledge).
        Asks user for confirmation when consequences are detected.
        """
        consequences = state.get("consequences", {})
        pending_action = state.get("pending_action", {})
        
        if not consequences or not consequences.get("has_consequences"):
            return {"messages": []}
        
        # Create confirmation message
        confirmation_message = consequences.get("message", "This action may have consequences. Do you want to proceed?")
        
        confirmation_msg = AIMessage(content=confirmation_message)
        
        return {"messages": [confirmation_msg]}
    
    def _route_after_confirmation(self, state: Dict[str, Any]) -> str:
        """Route after getting confirmation - check user response"""
        messages = state.get("messages", [])
        if not messages:
            return "agent"
        
        last_message = messages[-1]
        content = ""
        if hasattr(last_message, "content"):
            content = str(last_message.content).lower()
        else:
            content = str(last_message).lower()
        
        # Check if user confirmed
        if any(word in content for word in ["yes", "yep", "yeah", "confirm", "proceed", "ok", "okay", "sure"]):
            return "execute"
        elif any(word in content for word in ["no", "nope", "cancel", "abort", "stop"]):
            return "cancel"
        
        # If unclear, go back to agent
        return "agent"
    
    def _route_after_tools(self, state: Dict[str, Any]) -> str:
        """Route after tools execution"""
        # After tools execute, check if we need to check consequences
        # (This would be for actions that were executed)
        pending_action = state.get("pending_action")
        
        if pending_action:
            # If there was a pending action, we've executed it
            return "agent"
        
        # Check if there are more tool calls needed
        messages = state.get("messages", [])
        if messages:
            return "agent"
        
        return "end"
    
    async def _process_image_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process image node (Part 4: Vision Input).
        Analyzes uploaded image and extracts information.
        """
        image_data = state.get("image_data")
        messages = state.get("messages", [])
        current_state = state.get("state", "route_management")
        
        if not image_data:
            return {"messages": []}
        
        # Get user query from last message
        user_query = ""
        if messages:
            last_msg = messages[-1]
            if hasattr(last_msg, "content"):
                user_query = str(last_msg.content)
            else:
                user_query = str(last_msg)
        
        # Process image with vision tool
        vision_result = self.vision_tool.process_image(image_data, user_query)
        
        if vision_result.get("success"):
            # Match entities with database
            matched_result = self.vision_tool.match_entities_from_vision(vision_result, current_state)
            
            # Create message with extracted information
            extracted_info = matched_result.get("extracted_data", {})
            matched_entities = matched_result.get("matched_entities", {})
            
            info_message = f"""I've analyzed the image. Here's what I found:

Extracted Information:
- Suggested Action: {extracted_info.get('suggested_action', 'unknown')}
- Target Entity: {extracted_info.get('target_entity', 'none')}

Matched Entities:
- Trips: {len(matched_entities.get('trips', []))} found
- Routes: {len(matched_entities.get('routes', []))} found
- Vehicles: {len(matched_entities.get('vehicles', []))} found
- Drivers: {len(matched_entities.get('drivers', []))} found

Based on your request "{user_query}", I can help you with the suggested action."""
            
            vision_msg = AIMessage(content=info_message)
            
            # Add matched entities to state for tool execution
            return {
                "messages": [vision_msg],
                "image_data": None,  # Clear image data after processing
                "matched_entities": matched_entities,
                "suggested_action": extracted_info.get("suggested_action")
            }
        else:
            error_msg = AIMessage(content=f"I couldn't process the image: {vision_result.get('error', 'Unknown error')}")
            return {"messages": [error_msg], "image_data": None}
    
    def _should_continue(self, state: Dict[str, Any]) -> str:
        """Determine if agent should continue or end (legacy, kept for compatibility)"""
        messages = state.get("messages", [])
        last_message = messages[-1]
        
        # Check if there are tool calls
        tool_calls = getattr(last_message, "tool_calls", [])
        if tool_calls:
            return "continue"
        return "end"
    
    async def chat(
        self,
        message: str,
        state: str,
        thread_id: Optional[str] = None,
        image_base64: Optional[str] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Chat with the agent using streamable responses.
        
        Args:
            message: User message
            state: Current state (route_management or bus_dashboard)
            thread_id: Optional thread ID for conversation continuity
            image_base64: Optional base64 encoded image for vision processing (Part 4)
            
        Yields:
            Dict with streaming response data
        """
        if thread_id is None:
            thread_id = "default"
        
        config = {"configurable": {"thread_id": thread_id}}
        
        # Initial state - use dict format for messages initially
        initial_state = {
            "messages": [{"role": "user", "content": message}],
            "state": state,
            "pending_action": None,
            "consequences": None,
            "image_data": image_base64
        }
        
        # Stream graph execution
        try:
            async for event in self.graph.astream(initial_state, config):
                yield {
                    "type": "agent_update",
                    "data": event
                }
        except Exception as e:
            # Log error and yield error response
            import traceback
            error_trace = traceback.format_exc()
            print(f"LangGraph execution error: {error_trace}")
            
            # Get detailed error message
            error_msg = str(e) if e else "Unknown error"
            if not error_msg or error_msg.strip() == "":
                error_msg = f"Error type: {type(e).__name__}"
            
            # Extract more details from traceback if available
            error_lines = error_trace.split('\n')
            if len(error_lines) > 1:
                last_error_line = error_lines[-2] if len(error_lines) > 1 else error_lines[-1]
                if last_error_line.strip():
                    error_msg = f"{error_msg} - {last_error_line.strip()}"
            
            yield {
                "type": "final_response",
                "content": f"I encountered an error: {error_msg}. Please check the backend logs for details."
            }
            return
        
        # Get final state
        try:
            final_state = self.graph.get_state(config)
            final_messages = final_state.values.get("messages", [])
            
            # Debug: log message count
            print(f"Final messages count: {len(final_messages)}")
            if final_messages:
                print(f"Last message type: {type(final_messages[-1])}")
        except Exception as e:
            print(f"Error getting final state: {e}")
            final_messages = []
        
        # Extract final response - look for AIMessage with content
        final_response = None
        for msg in reversed(final_messages):
            # Handle different message formats
            if hasattr(msg, "content"):
                content = msg.content
                if content and isinstance(content, str) and content.strip():
                    final_response = content
                    break
            elif isinstance(msg, dict):
                content = msg.get("content", "")
                if content and isinstance(content, str) and content.strip():
                    final_response = content
                    break
            elif isinstance(msg, str):
                if msg.strip():
                    final_response = msg
                    break
        
        # If no response found, try to get last AI message
        if not final_response:
            for msg in reversed(final_messages):
                if isinstance(msg, AIMessage):
                    if hasattr(msg, "content") and msg.content:
                        final_response = str(msg.content)
                        break
        
        # If still no response, check if we have any messages at all
        if not final_response:
            if final_messages:
                # Try to get any message content
                for msg in final_messages:
                    if isinstance(msg, dict):
                        content = msg.get("content", "")
                        if content:
                            final_response = str(content)
                            break
                    elif hasattr(msg, "__str__"):
                        msg_str = str(msg)
                        if msg_str and len(msg_str) > 10:  # Meaningful content
                            final_response = msg_str
                            break
        
        # Last resort: create a helpful default response
        if not final_response or not final_response.strip():
            final_response = "I received your message. How can I assist you with the transport management system?"
        
        yield {
            "type": "final_response",
            "content": final_response
        }


# Global client instance
_langgraph_client: Optional[LangGraphMCPClient] = None


def get_langgraph_client() -> LangGraphMCPClient:
    """Get or create LangGraph MCP client instance"""
    global _langgraph_client
    if _langgraph_client is None:
        _langgraph_client = LangGraphMCPClient()
    return _langgraph_client

