"""
MCP Tools for Route Management page.
Includes tools for stops, paths, and routes operations.
"""

from typing import Dict, Any, List
from backend.mcp.types import Tool, TextContent
from backend.mcp.orchestration import SupabaseOrchestrator


# State constant for Route Management
ROUTE_MANAGEMENT_STATE = "route_management"


class RouteManagementTools:
    """MCP Tools for Route Management operations"""
    
    def __init__(self):
        self.orchestrator = SupabaseOrchestrator()
        self.state = ROUTE_MANAGEMENT_STATE
    
    def get_tools(self) -> List[Tool]:
        """Get all route management tools"""
        return [
            Tool(
                name="list_stops",
                description="List all active stops. Use this to see available stops for creating paths and routes.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="get_stop",
                description="Get details of a specific stop by ID.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "stop_id": {
                            "type": "integer",
                            "description": "The ID of the stop to retrieve"
                        }
                    },
                    "required": ["stop_id"]
                }
            ),
            Tool(
                name="create_stop",
                description="Create a new stop with name, coordinates, and optional description/address.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Stop name"},
                        "latitude": {"type": "number", "description": "Latitude coordinate (-90 to 90)"},
                        "longitude": {"type": "number", "description": "Longitude coordinate (-180 to 180)"},
                        "description": {"type": "string", "description": "Optional stop description"},
                        "address": {"type": "string", "description": "Optional stop address"},
                        "created_by": {"type": "integer", "description": "User ID creating the stop", "default": 1}
                    },
                    "required": ["name", "latitude", "longitude"]
                }
            ),
            Tool(
                name="update_stop",
                description="Update an existing stop's information.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "stop_id": {"type": "integer", "description": "Stop ID to update"},
                        "name": {"type": "string", "description": "Updated stop name"},
                        "latitude": {"type": "number", "description": "Updated latitude"},
                        "longitude": {"type": "number", "description": "Updated longitude"},
                        "description": {"type": "string", "description": "Updated description"},
                        "address": {"type": "string", "description": "Updated address"},
                        "updated_by": {"type": "integer", "description": "User ID updating the stop", "default": 1}
                    },
                    "required": ["stop_id"]
                }
            ),
            Tool(
                name="delete_stop",
                description="Soft delete a stop (marks as deleted but doesn't remove from database).",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "stop_id": {"type": "integer", "description": "Stop ID to delete"},
                        "deleted_by": {"type": "integer", "description": "User ID deleting the stop", "default": 1}
                    },
                    "required": ["stop_id"]
                }
            ),
            Tool(
                name="list_paths",
                description="List all active paths. Paths are ordered sequences of stops.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="get_path",
                description="Get details of a specific path by ID.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "path_id": {
                            "type": "integer",
                            "description": "The ID of the path to retrieve"
                        }
                    },
                    "required": ["path_id"]
                }
            ),
            Tool(
                name="create_path",
                description="Create a new path with name, ordered list of stop IDs, distance, and duration.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "path_name": {"type": "string", "description": "Path name"},
                        "ordered_list_of_stop_ids": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "Ordered list of stop IDs in the path"
                        },
                        "description": {"type": "string", "description": "Optional path description"},
                        "total_distance_km": {"type": "number", "description": "Total distance in kilometers"},
                        "estimated_duration_minutes": {"type": "integer", "description": "Estimated duration in minutes"},
                        "created_by": {"type": "integer", "description": "User ID creating the path", "default": 1}
                    },
                    "required": ["path_name", "ordered_list_of_stop_ids"]
                }
            ),
            Tool(
                name="update_path",
                description="Update an existing path's information.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "path_id": {"type": "integer", "description": "Path ID to update"},
                        "path_name": {"type": "string", "description": "Updated path name"},
                        "ordered_list_of_stop_ids": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "Updated ordered list of stop IDs"
                        },
                        "description": {"type": "string", "description": "Updated description"},
                        "total_distance_km": {"type": "number", "description": "Updated distance"},
                        "estimated_duration_minutes": {"type": "integer", "description": "Updated duration"},
                        "updated_by": {"type": "integer", "description": "User ID updating the path", "default": 1}
                    },
                    "required": ["path_id"]
                }
            ),
            Tool(
                name="delete_path",
                description="Soft delete a path.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "path_id": {"type": "integer", "description": "Path ID to delete"},
                        "deleted_by": {"type": "integer", "description": "User ID deleting the path", "default": 1}
                    },
                    "required": ["path_id"]
                }
            ),
            Tool(
                name="list_routes",
                description="List all active routes. Routes are paths with assigned times and operational details.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="get_route",
                description="Get details of a specific route by ID.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "route_id": {
                            "type": "integer",
                            "description": "The ID of the route to retrieve"
                        }
                    },
                    "required": ["route_id"]
                }
            ),
            Tool(
                name="create_route",
                description="Create a new route with path, shift time, direction, and start/end points.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "path_id": {"type": "integer", "description": "Path ID for this route"},
                        "route_display_name": {"type": "string", "description": "Display name for the route"},
                        "shift_time": {"type": "string", "description": "Shift time in HH:MM:SS format"},
                        "direction": {"type": "string", "description": "Route direction (e.g., 'outbound', 'inbound')"},
                        "start_point": {"type": "string", "description": "Starting point name"},
                        "end_point": {"type": "string", "description": "Ending point name"},
                        "status": {"type": "string", "description": "Route status", "default": "active"},
                        "notes": {"type": "string", "description": "Optional notes"},
                        "created_by": {"type": "integer", "description": "User ID creating the route", "default": 1}
                    },
                    "required": ["path_id", "route_display_name", "shift_time", "direction", "start_point", "end_point"]
                }
            ),
            Tool(
                name="update_route",
                description="Update an existing route's information.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "route_id": {"type": "integer", "description": "Route ID to update"},
                        "path_id": {"type": "integer", "description": "Updated path ID"},
                        "route_display_name": {"type": "string", "description": "Updated display name"},
                        "shift_time": {"type": "string", "description": "Updated shift time in HH:MM:SS format"},
                        "direction": {"type": "string", "description": "Updated direction"},
                        "start_point": {"type": "string", "description": "Updated start point"},
                        "end_point": {"type": "string", "description": "Updated end point"},
                        "status": {"type": "string", "description": "Updated status"},
                        "notes": {"type": "string", "description": "Updated notes"},
                        "updated_by": {"type": "integer", "description": "User ID updating the route", "default": 1}
                    },
                    "required": ["route_id"]
                }
            ),
            Tool(
                name="delete_route",
                description="Soft delete a route.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "route_id": {"type": "integer", "description": "Route ID to delete"},
                        "deleted_by": {"type": "integer", "description": "User ID deleting the route", "default": 1}
                    },
                    "required": ["route_id"]
                }
            )
        ]
    
    async def call_tool(self, name: str, arguments: Dict[str, Any], state: str) -> List[TextContent]:
        """
        Execute a route management tool.
        
        Args:
            name: Tool name
            arguments: Tool arguments
            state: Current state (must match ROUTE_MANAGEMENT_STATE)
            
        Returns:
            List of text content with tool results
        """
        # State validation (Layer 5.2)
        if state != ROUTE_MANAGEMENT_STATE:
            return [TextContent(
                type="text",
                text=f"Error: Tool '{name}' is only available for route_management state. Current state: {state}"
            )]
        
        try:
            # Stops operations
            if name == "list_stops":
                stops = self.orchestrator.get_stops()
                return [TextContent(type="text", text=f"Found {len(stops)} stops: {stops}")]
            
            elif name == "get_stop":
                stop = self.orchestrator.get_stop_by_id(arguments["stop_id"])
                if stop:
                    return [TextContent(type="text", text=f"Stop details: {stop}")]
                return [TextContent(type="text", text=f"Stop {arguments['stop_id']} not found")]
            
            elif name == "create_stop":
                result = self.orchestrator.create_stop(
                    arguments,
                    created_by=arguments.get("created_by", 1)
                )
                return [TextContent(type="text", text=f"Stop created successfully: {result}")]
            
            elif name == "update_stop":
                stop_id = arguments.pop("stop_id")
                result = self.orchestrator.update_stop(
                    stop_id,
                    arguments,
                    updated_by=arguments.get("updated_by", 1)
                )
                return [TextContent(type="text", text=f"Stop updated successfully: {result}")]
            
            elif name == "delete_stop":
                result = self.orchestrator.delete_stop(
                    arguments["stop_id"],
                    deleted_by=arguments.get("deleted_by", 1)
                )
                return [TextContent(type="text", text=f"Stop deleted successfully: {result}")]
            
            # Paths operations
            elif name == "list_paths":
                paths = self.orchestrator.get_paths()
                return [TextContent(type="text", text=f"Found {len(paths)} paths: {paths}")]
            
            elif name == "get_path":
                path = self.orchestrator.get_path_by_id(arguments["path_id"])
                if path:
                    return [TextContent(type="text", text=f"Path details: {path}")]
                return [TextContent(type="text", text=f"Path {arguments['path_id']} not found")]
            
            elif name == "create_path":
                result = self.orchestrator.create_path(
                    arguments,
                    created_by=arguments.get("created_by", 1)
                )
                return [TextContent(type="text", text=f"Path created successfully: {result}")]
            
            elif name == "update_path":
                path_id = arguments.pop("path_id")
                result = self.orchestrator.update_path(
                    path_id,
                    arguments,
                    updated_by=arguments.get("updated_by", 1)
                )
                return [TextContent(type="text", text=f"Path updated successfully: {result}")]
            
            elif name == "delete_path":
                result = self.orchestrator.delete_path(
                    arguments["path_id"],
                    deleted_by=arguments.get("deleted_by", 1)
                )
                return [TextContent(type="text", text=f"Path deleted successfully: {result}")]
            
            # Routes operations
            elif name == "list_routes":
                routes = self.orchestrator.get_routes()
                return [TextContent(type="text", text=f"Found {len(routes)} routes: {routes}")]
            
            elif name == "get_route":
                route = self.orchestrator.get_route_by_id(arguments["route_id"])
                if route:
                    return [TextContent(type="text", text=f"Route details: {route}")]
                return [TextContent(type="text", text=f"Route {arguments['route_id']} not found")]
            
            elif name == "create_route":
                result = self.orchestrator.create_route(
                    arguments,
                    created_by=arguments.get("created_by", 1)
                )
                return [TextContent(type="text", text=f"Route created successfully: {result}")]
            
            elif name == "update_route":
                route_id = arguments.pop("route_id")
                result = self.orchestrator.update_route(
                    route_id,
                    arguments,
                    updated_by=arguments.get("updated_by", 1)
                )
                return [TextContent(type="text", text=f"Route updated successfully: {result}")]
            
            elif name == "delete_route":
                result = self.orchestrator.delete_route(
                    arguments["route_id"],
                    deleted_by=arguments.get("deleted_by", 1)
                )
                return [TextContent(type="text", text=f"Route deleted successfully: {result}")]
            
            else:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]
                
        except Exception as e:
            return [TextContent(type="text", text=f"Error executing tool {name}: {str(e)}")]

