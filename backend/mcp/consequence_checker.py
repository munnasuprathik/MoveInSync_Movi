"""
Consequence checker for "Tribal Knowledge" flow.
Checks for consequences before executing actions that might affect bookings or trip sheets.
"""

from typing import Dict, Any, Optional
from backend.mcp.orchestration import SupabaseOrchestrator


class ConsequenceChecker:
    """
    Checks consequences of actions before execution.
    Implements the "Tribal Knowledge" flow from Part 3.
    """
    
    def __init__(self):
        self.orchestrator = SupabaseOrchestrator()
    
    def check_deployment_removal_consequences(
        self,
        trip_id: int,
        deployment_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Check consequences of removing a vehicle/driver from a trip.
        
        Returns:
            Dict with:
            - has_consequences: bool
            - booking_percentage: float
            - total_bookings: int
            - trip_status: str
            - message: str (warning message if consequences exist)
        """
        # Get trip details
        trip = self.orchestrator.get_trip_by_id(trip_id)
        if not trip:
            return {
                "has_consequences": False,
                "message": "Trip not found"
            }
        
        booking_percentage = trip.get("booking_status_percentage", 0) or 0
        # Calculate total_bookings from booking_percentage if not available
        # Assuming capacity is 50 for estimation (can be improved)
        total_bookings = trip.get("total_bookings", 0) or int((booking_percentage / 100) * 50) if booking_percentage > 0 else 0
        trip_status = trip.get("status", "scheduled")
        trip_name = trip.get("display_name", f"Trip {trip_id}")
        
        # Check if there are consequences
        has_consequences = False
        consequences = []
        
        # Consequence 1: Trip has bookings
        if booking_percentage > 0 or total_bookings > 0:
            has_consequences = True
            consequences.append(
                f"Trip '{trip_name}' is {booking_percentage}% booked ({total_bookings} bookings)"
            )
        
        # Consequence 2: Trip is scheduled or in progress
        if trip_status in ["scheduled", "in_progress"]:
            if not has_consequences:
                has_consequences = True
            consequences.append(f"Trip is currently {trip_status}")
        
        # Build warning message
        message = ""
        if has_consequences:
            message = (
                f"I can remove the vehicle. However, please be aware that "
                f"'{trip_name}' is already {booking_percentage}% booked by employees "
                f"({total_bookings} bookings). Removing the vehicle will cancel these bookings "
                f"and a trip-sheet will fail to generate. Do you want to proceed?"
            )
        
        return {
            "has_consequences": has_consequences,
            "booking_percentage": booking_percentage,
            "total_bookings": total_bookings,
            "trip_status": trip_status,
            "trip_name": trip_name,
            "message": message,
            "consequences": consequences
        }
    
    def check_trip_deletion_consequences(self, trip_id: int) -> Dict[str, Any]:
        """Check consequences of deleting a trip"""
        return self.check_deployment_removal_consequences(trip_id)
    
    def check_route_deletion_consequences(self, route_id: int) -> Dict[str, Any]:
        """
        Check consequences of deleting a route.
        Returns consequences if route has active trips.
        """
        route = self.orchestrator.get_route_by_id(route_id)
        if not route:
            return {
                "has_consequences": False,
                "message": "Route not found"
            }
        
        # Get all trips for this route
        trips = self.orchestrator.get_trips()
        route_trips = [t for t in trips if t.get("route_id") == route_id]
        
        active_trips = [t for t in route_trips if t.get("status") in ["scheduled", "in_progress"]]
        trips_with_bookings = [t for t in route_trips if (t.get("booking_status_percentage", 0) or 0) > 0]
        
        has_consequences = len(active_trips) > 0 or len(trips_with_bookings) > 0
        
        message = ""
        if has_consequences:
            route_name = route.get("route_display_name", f"Route {route_id}")
            message = (
                f"I can delete the route '{route_name}'. However, this route has "
                f"{len(active_trips)} active trips and {len(trips_with_bookings)} trips with bookings. "
                f"Deleting this route will affect these trips. Do you want to proceed?"
            )
        
        return {
            "has_consequences": has_consequences,
            "active_trips_count": len(active_trips),
            "trips_with_bookings_count": len(trips_with_bookings),
            "message": message
        }
    
    def check_path_deletion_consequences(self, path_id: int) -> Dict[str, Any]:
        """
        Check consequences of deleting a path.
        Returns consequences if path is used by routes.
        """
        path = self.orchestrator.get_path_by_id(path_id)
        if not path:
            return {
                "has_consequences": False,
                "message": "Path not found"
            }
        
        # Get all routes using this path
        routes = self.orchestrator.get_routes()
        path_routes = [r for r in routes if r.get("path_id") == path_id]
        
        has_consequences = len(path_routes) > 0
        
        message = ""
        if has_consequences:
            path_name = path.get("path_name", f"Path {path_id}")
            message = (
                f"I can delete the path '{path_name}'. However, this path is used by "
                f"{len(path_routes)} routes. Deleting this path will affect these routes. "
                f"Do you want to proceed?"
            )
        
        return {
            "has_consequences": has_consequences,
            "routes_count": len(path_routes),
            "message": message
        }

