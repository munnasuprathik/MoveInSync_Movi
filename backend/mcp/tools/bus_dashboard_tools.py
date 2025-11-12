"""
MCP Tools for Bus Dashboard page.
Includes tools for vehicles, drivers, trips, and deployments operations.
"""

from typing import Dict, Any, List
from backend.mcp.types import Tool, TextContent
from backend.mcp.orchestration import SupabaseOrchestrator


# State constant for Bus Dashboard
BUS_DASHBOARD_STATE = "bus_dashboard"


class BusDashboardTools:
    """MCP Tools for Bus Dashboard operations"""
    
    def __init__(self):
        self.orchestrator = SupabaseOrchestrator()
        self.state = BUS_DASHBOARD_STATE
    
    def get_tools(self) -> List[Tool]:
        """Get all bus dashboard tools"""
        return [
            # Vehicles tools
            Tool(
                name="list_vehicles",
                description="List all active vehicles (buses).",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="get_vehicle",
                description="Get details of a specific vehicle by ID.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "vehicle_id": {
                            "type": "integer",
                            "description": "The ID of the vehicle to retrieve"
                        }
                    },
                    "required": ["vehicle_id"]
                }
            ),
            Tool(
                name="create_vehicle",
                description="Create a new vehicle with license plate, type, capacity, and other details.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "license_plate": {"type": "string", "description": "Vehicle license plate"},
                        "type": {"type": "string", "description": "Vehicle type (e.g., 'Bus')"},
                        "capacity": {"type": "integer", "description": "Passenger capacity"},
                        "make": {"type": "string", "description": "Vehicle make"},
                        "model": {"type": "string", "description": "Vehicle model"},
                        "year": {"type": "integer", "description": "Manufacturing year"},
                        "color": {"type": "string", "description": "Vehicle color"},
                        "is_available": {"type": "boolean", "description": "Availability status", "default": True},
                        "status": {"type": "string", "description": "Vehicle status", "default": "active"},
                        "notes": {"type": "string", "description": "Optional notes"},
                        "created_by": {"type": "integer", "description": "User ID creating the vehicle", "default": 1}
                    },
                    "required": ["license_plate", "type", "capacity"]
                }
            ),
            Tool(
                name="update_vehicle",
                description="Update an existing vehicle's information.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "vehicle_id": {"type": "integer", "description": "Vehicle ID to update"},
                        "license_plate": {"type": "string", "description": "Updated license plate"},
                        "type": {"type": "string", "description": "Updated vehicle type"},
                        "capacity": {"type": "integer", "description": "Updated capacity"},
                        "make": {"type": "string", "description": "Updated make"},
                        "model": {"type": "string", "description": "Updated model"},
                        "year": {"type": "integer", "description": "Updated year"},
                        "color": {"type": "string", "description": "Updated color"},
                        "is_available": {"type": "boolean", "description": "Updated availability"},
                        "status": {"type": "string", "description": "Updated status"},
                        "notes": {"type": "string", "description": "Updated notes"},
                        "updated_by": {"type": "integer", "description": "User ID updating the vehicle", "default": 1}
                    },
                    "required": ["vehicle_id"]
                }
            ),
            Tool(
                name="delete_vehicle",
                description="Soft delete a vehicle.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "vehicle_id": {"type": "integer", "description": "Vehicle ID to delete"},
                        "deleted_by": {"type": "integer", "description": "User ID deleting the vehicle", "default": 1}
                    },
                    "required": ["vehicle_id"]
                }
            ),
            # Drivers tools
            Tool(
                name="list_drivers",
                description="List all active drivers.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="get_driver",
                description="Get details of a specific driver by ID.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "driver_id": {
                            "type": "integer",
                            "description": "The ID of the driver to retrieve"
                        }
                    },
                    "required": ["driver_id"]
                }
            ),
            Tool(
                name="create_driver",
                description="Create a new driver with name, contact info, and license details.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Driver full name"},
                        "phone_number": {"type": "string", "description": "Phone number"},
                        "email": {"type": "string", "description": "Email address"},
                        "license_number": {"type": "string", "description": "Driver license number"},
                        "is_available": {"type": "boolean", "description": "Availability status", "default": True},
                        "status": {"type": "string", "description": "Driver status", "default": "active"},
                        "notes": {"type": "string", "description": "Optional notes"},
                        "created_by": {"type": "integer", "description": "User ID creating the driver", "default": 1}
                    },
                    "required": ["name", "phone_number"]
                }
            ),
            Tool(
                name="update_driver",
                description="Update an existing driver's information.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "driver_id": {"type": "integer", "description": "Driver ID to update"},
                        "name": {"type": "string", "description": "Updated name"},
                        "phone_number": {"type": "string", "description": "Updated phone number"},
                        "email": {"type": "string", "description": "Updated email"},
                        "license_number": {"type": "string", "description": "Updated license number"},
                        "is_available": {"type": "boolean", "description": "Updated availability"},
                        "status": {"type": "string", "description": "Updated status"},
                        "notes": {"type": "string", "description": "Updated notes"},
                        "updated_by": {"type": "integer", "description": "User ID updating the driver", "default": 1}
                    },
                    "required": ["driver_id"]
                }
            ),
            Tool(
                name="delete_driver",
                description="Soft delete a driver.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "driver_id": {"type": "integer", "description": "Driver ID to delete"},
                        "deleted_by": {"type": "integer", "description": "User ID deleting the driver", "default": 1}
                    },
                    "required": ["driver_id"]
                }
            ),
            # Trips tools
            Tool(
                name="list_trips",
                description="List all active trips with their status, dates, and booking information. Returns total count and trip details.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="get_trip_count",
                description="Get the total count of active trips in the system. Use this when the user asks 'how many trips' or 'total trips'.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="get_scheduled_trips",
                description="Get all trips with status 'scheduled'. Use this when the user asks for scheduled trips.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="get_trip",
                description="Get details of a specific trip by ID.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "trip_id": {
                            "type": "integer",
                            "description": "The ID of the trip to retrieve"
                        }
                    },
                    "required": ["trip_id"]
                }
            ),
            Tool(
                name="create_trip",
                description="Create a new trip with route, date, and booking information.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "route_id": {"type": "integer", "description": "Route ID for this trip"},
                        "display_name": {"type": "string", "description": "Trip display name"},
                        "trip_date": {"type": "string", "description": "Trip date in YYYY-MM-DD format"},
                        "booking_status_percentage": {"type": "number", "description": "Booking percentage (0-100)", "default": 0},
                        "live_status": {"type": "string", "description": "Current live status"},
                        "total_bookings": {"type": "integer", "description": "Total number of bookings", "default": 0},
                        "status": {"type": "string", "description": "Trip status", "default": "scheduled"},
                        "notes": {"type": "string", "description": "Optional notes"},
                        "created_by": {"type": "integer", "description": "User ID creating the trip", "default": 1}
                    },
                    "required": ["route_id", "display_name", "trip_date"]
                }
            ),
            Tool(
                name="update_trip",
                description="Update an existing trip's information, including status and booking details.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "trip_id": {"type": "integer", "description": "Trip ID to update"},
                        "route_id": {"type": "integer", "description": "Updated route ID"},
                        "display_name": {"type": "string", "description": "Updated display name"},
                        "trip_date": {"type": "string", "description": "Updated trip date"},
                        "booking_status_percentage": {"type": "number", "description": "Updated booking percentage"},
                        "live_status": {"type": "string", "description": "Updated live status"},
                        "total_bookings": {"type": "integer", "description": "Updated total bookings"},
                        "status": {"type": "string", "description": "Updated status"},
                        "notes": {"type": "string", "description": "Updated notes"},
                        "updated_by": {"type": "integer", "description": "User ID updating the trip", "default": 1}
                    },
                    "required": ["trip_id"]
                }
            ),
            Tool(
                name="delete_trip",
                description="Soft delete a trip.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "trip_id": {"type": "integer", "description": "Trip ID to delete"},
                        "deleted_by": {"type": "integer", "description": "User ID deleting the trip", "default": 1}
                    },
                    "required": ["trip_id"]
                }
            ),
            # Deployments tools
            Tool(
                name="list_deployments",
                description="List all active deployments (vehicle and driver assignments to trips).",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="get_deployment",
                description="Get details of a specific deployment by ID.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "deployment_id": {
                            "type": "integer",
                            "description": "The ID of the deployment to retrieve"
                        }
                    },
                    "required": ["deployment_id"]
                }
            ),
            Tool(
                name="get_deployment_by_trip",
                description="Get deployment details for a specific trip.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "trip_id": {
                            "type": "integer",
                            "description": "The trip ID to get deployment for"
                        }
                    },
                    "required": ["trip_id"]
                }
            ),
            Tool(
                name="create_deployment",
                description="Create a new deployment (assign vehicle and driver to a trip).",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "trip_id": {"type": "integer", "description": "Trip ID to assign"},
                        "vehicle_id": {"type": "integer", "description": "Vehicle ID to assign"},
                        "driver_id": {"type": "integer", "description": "Driver ID to assign"},
                        "deployment_status": {"type": "string", "description": "Deployment status", "default": "assigned"},
                        "notes": {"type": "string", "description": "Optional notes"},
                        "created_by": {"type": "integer", "description": "User ID creating the deployment", "default": 1}
                    },
                    "required": ["trip_id", "vehicle_id", "driver_id"]
                }
            ),
            Tool(
                name="update_deployment",
                description="Update an existing deployment (reassign vehicle/driver or change status).",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "deployment_id": {"type": "integer", "description": "Deployment ID to update"},
                        "trip_id": {"type": "integer", "description": "Updated trip ID"},
                        "vehicle_id": {"type": "integer", "description": "Updated vehicle ID"},
                        "driver_id": {"type": "integer", "description": "Updated driver ID"},
                        "deployment_status": {"type": "string", "description": "Updated deployment status"},
                        "notes": {"type": "string", "description": "Updated notes"},
                        "updated_by": {"type": "integer", "description": "User ID updating the deployment", "default": 1}
                    },
                    "required": ["deployment_id"]
                }
            ),
            Tool(
                name="delete_deployment",
                description="Soft delete a deployment (unassign vehicle/driver from trip).",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "deployment_id": {"type": "integer", "description": "Deployment ID to delete"},
                        "deleted_by": {"type": "integer", "description": "User ID deleting the deployment", "default": 1}
                    },
                    "required": ["deployment_id"]
                }
            )
        ]
    
    async def call_tool(self, name: str, arguments: Dict[str, Any], state: str) -> List[TextContent]:
        """
        Execute a bus dashboard tool.
        
        Args:
            name: Tool name
            arguments: Tool arguments
            state: Current state (must match BUS_DASHBOARD_STATE)
            
        Returns:
            List of text content with tool results
        """
        # State validation (Layer 5.2)
        if state != BUS_DASHBOARD_STATE:
            return [TextContent(
                type="text",
                text=f"Error: Tool '{name}' is only available for bus_dashboard state. Current state: {state}"
            )]
        
        try:
            # Vehicles operations
            if name == "list_vehicles":
                vehicles = self.orchestrator.get_vehicles()
                return [TextContent(type="text", text=f"Found {len(vehicles)} vehicles: {vehicles}")]
            
            elif name == "get_vehicle":
                vehicle = self.orchestrator.get_vehicle_by_id(arguments["vehicle_id"])
                if vehicle:
                    return [TextContent(type="text", text=f"Vehicle details: {vehicle}")]
                return [TextContent(type="text", text=f"Vehicle {arguments['vehicle_id']} not found")]
            
            elif name == "create_vehicle":
                result = self.orchestrator.create_vehicle(
                    arguments,
                    created_by=arguments.get("created_by", 1)
                )
                return [TextContent(type="text", text=f"Vehicle created successfully: {result}")]
            
            elif name == "update_vehicle":
                vehicle_id = arguments.pop("vehicle_id")
                result = self.orchestrator.update_vehicle(
                    vehicle_id,
                    arguments,
                    updated_by=arguments.get("updated_by", 1)
                )
                return [TextContent(type="text", text=f"Vehicle updated successfully: {result}")]
            
            elif name == "delete_vehicle":
                result = self.orchestrator.delete_vehicle(
                    arguments["vehicle_id"],
                    deleted_by=arguments.get("deleted_by", 1)
                )
                return [TextContent(type="text", text=f"Vehicle deleted successfully: {result}")]
            
            # Drivers operations
            elif name == "list_drivers":
                drivers = self.orchestrator.get_drivers()
                return [TextContent(type="text", text=f"Found {len(drivers)} drivers: {drivers}")]
            
            elif name == "get_driver":
                driver = self.orchestrator.get_driver_by_id(arguments["driver_id"])
                if driver:
                    return [TextContent(type="text", text=f"Driver details: {driver}")]
                return [TextContent(type="text", text=f"Driver {arguments['driver_id']} not found")]
            
            elif name == "create_driver":
                result = self.orchestrator.create_driver(
                    arguments,
                    created_by=arguments.get("created_by", 1)
                )
                return [TextContent(type="text", text=f"Driver created successfully: {result}")]
            
            elif name == "update_driver":
                driver_id = arguments.pop("driver_id")
                result = self.orchestrator.update_driver(
                    driver_id,
                    arguments,
                    updated_by=arguments.get("updated_by", 1)
                )
                return [TextContent(type="text", text=f"Driver updated successfully: {result}")]
            
            elif name == "delete_driver":
                result = self.orchestrator.delete_driver(
                    arguments["driver_id"],
                    deleted_by=arguments.get("deleted_by", 1)
                )
                return [TextContent(type="text", text=f"Driver deleted successfully: {result}")]
            
            # Trips operations
            elif name == "list_trips":
                try:
                    trips = self.orchestrator.get_trips()
                    trip_count = len(trips)
                    if trip_count == 0:
                        return [TextContent(type="text", text="Total trips: 0\n\nNo trips found in the system. Please check if data has been initialized in Supabase.")]
                    # Format response with count prominently displayed
                    response = f"Total trips: {trip_count}\n\n"
                    if trip_count <= 10:
                        # Show all trips if 10 or fewer
                        response += f"Trips list:\n{trips}"
                    else:
                        # Show summary if more than 10
                        response += f"Showing first 5 of {trip_count} trips:\n{trips[:5]}\n\n... and {trip_count - 5} more trips"
                    return [TextContent(type="text", text=response)]
                except Exception as e:
                    error_msg = str(e)
                    return [TextContent(type="text", text=f"Error fetching trips from Supabase: {error_msg}\n\nPlease ensure:\n1. SUPABASE_URL and SUPABASE_KEY are set in .env file\n2. Database schema has been created\n3. Data has been initialized (run database/init_database.py if needed)")]
            
            elif name == "get_trip_count":
                try:
                    trips = self.orchestrator.get_trips()
                    trip_count = len(trips)
                    return [TextContent(type="text", text=f"Total number of trips: {trip_count}")]
                except Exception as e:
                    error_msg = str(e)
                    return [TextContent(type="text", text=f"Error fetching trip count from Supabase: {error_msg}\n\nPlease check your Supabase connection and ensure data has been initialized.")]
            
            elif name == "get_scheduled_trips":
                try:
                    trips = self.orchestrator.get_trips()
                    scheduled_trips = [trip for trip in trips if trip.get("status", "").lower() == "scheduled"]
                    scheduled_count = len(scheduled_trips)
                    if scheduled_count == 0:
                        return [TextContent(type="text", text="Scheduled trips: 0\n\nNo scheduled trips found in the system.")]
                    response = f"Scheduled trips: {scheduled_count}\n\n"
                    if scheduled_count <= 10:
                        response += f"Scheduled trips list:\n{scheduled_trips}"
                    else:
                        response += f"Showing first 5 of {scheduled_count} scheduled trips:\n{scheduled_trips[:5]}\n\n... and {scheduled_count - 5} more scheduled trips"
                    return [TextContent(type="text", text=response)]
                except Exception as e:
                    error_msg = str(e)
                    return [TextContent(type="text", text=f"Error fetching scheduled trips from Supabase: {error_msg}\n\nPlease check your Supabase connection and ensure data has been initialized.")]
            
            elif name == "get_trip":
                trip = self.orchestrator.get_trip_by_id(arguments["trip_id"])
                if trip:
                    return [TextContent(type="text", text=f"Trip details: {trip}")]
                return [TextContent(type="text", text=f"Trip {arguments['trip_id']} not found")]
            
            elif name == "create_trip":
                result = self.orchestrator.create_trip(
                    arguments,
                    created_by=arguments.get("created_by", 1)
                )
                return [TextContent(type="text", text=f"Trip created successfully: {result}")]
            
            elif name == "update_trip":
                trip_id = arguments.pop("trip_id")
                result = self.orchestrator.update_trip(
                    trip_id,
                    arguments,
                    updated_by=arguments.get("updated_by", 1)
                )
                return [TextContent(type="text", text=f"Trip updated successfully: {result}")]
            
            elif name == "delete_trip":
                result = self.orchestrator.delete_trip(
                    arguments["trip_id"],
                    deleted_by=arguments.get("deleted_by", 1)
                )
                return [TextContent(type="text", text=f"Trip deleted successfully: {result}")]
            
            # Deployments operations
            elif name == "list_deployments":
                deployments = self.orchestrator.get_deployments()
                return [TextContent(type="text", text=f"Found {len(deployments)} deployments: {deployments}")]
            
            elif name == "get_deployment":
                deployment = self.orchestrator.get_deployment_by_id(arguments["deployment_id"])
                if deployment:
                    return [TextContent(type="text", text=f"Deployment details: {deployment}")]
                return [TextContent(type="text", text=f"Deployment {arguments['deployment_id']} not found")]
            
            elif name == "get_deployment_by_trip":
                deployment = self.orchestrator.get_deployment_by_trip(arguments["trip_id"])
                if deployment:
                    return [TextContent(type="text", text=f"Deployment for trip {arguments['trip_id']}: {deployment}")]
                return [TextContent(type="text", text=f"No deployment found for trip {arguments['trip_id']}")]
            
            elif name == "create_deployment":
                result = self.orchestrator.create_deployment(
                    arguments,
                    created_by=arguments.get("created_by", 1)
                )
                return [TextContent(type="text", text=f"Deployment created successfully: {result}")]
            
            elif name == "update_deployment":
                deployment_id = arguments.pop("deployment_id")
                result = self.orchestrator.update_deployment(
                    deployment_id,
                    arguments,
                    updated_by=arguments.get("updated_by", 1)
                )
                return [TextContent(type="text", text=f"Deployment updated successfully: {result}")]
            
            elif name == "delete_deployment":
                result = self.orchestrator.delete_deployment(
                    arguments["deployment_id"],
                    deleted_by=arguments.get("deleted_by", 1)
                )
                return [TextContent(type="text", text=f"Deployment deleted successfully: {result}")]
            
            else:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]
                
        except Exception as e:
            return [TextContent(type="text", text=f"Error executing tool {name}: {str(e)}")]

