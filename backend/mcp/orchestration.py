"""
Reusable Supabase orchestration layer for MCP tools.

This module provides a unified interface for all Supabase operations,
making it reusable across all MCP tools.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from database import (
    StopsRepository,
    PathsRepository,
    RoutesRepository,
    VehiclesRepository,
    DriversRepository,
    TripsRepository,
    DeploymentsRepository
)


class SupabaseOrchestrator:
    """
    Centralized Supabase orchestration layer.
    Provides reusable database operations for all MCP tools.
    """
    
    def __init__(self):
        self.stops_repo = StopsRepository()
        self.paths_repo = PathsRepository()
        self.routes_repo = RoutesRepository()
        self.vehicles_repo = VehiclesRepository()
        self.drivers_repo = DriversRepository()
        self.trips_repo = TripsRepository()
        self.deployments_repo = DeploymentsRepository()
    
    # Stops operations
    def get_stops(self) -> List[Dict[str, Any]]:
        """Get all active stops"""
        return self.stops_repo.get_all_active()
    
    def get_stop_by_id(self, stop_id: int) -> Optional[Dict[str, Any]]:
        """Get stop by ID"""
        return self.stops_repo.get_by_id(stop_id)
    
    def create_stop(self, data: Dict[str, Any], created_by: int = 1) -> Dict[str, Any]:
        """Create a new stop"""
        data["created_by"] = created_by
        return self.stops_repo.create(data)
    
    def update_stop(self, stop_id: int, data: Dict[str, Any], updated_by: int = 1) -> Dict[str, Any]:
        """Update a stop"""
        data["updated_by"] = updated_by
        return self.stops_repo.update(stop_id, data)
    
    def delete_stop(self, stop_id: int, deleted_by: int = 1) -> Dict[str, Any]:
        """Soft delete a stop"""
        return self.stops_repo.soft_delete(stop_id, deleted_by)
    
    # Paths operations
    def get_paths(self) -> List[Dict[str, Any]]:
        """Get all active paths"""
        return self.paths_repo.get_all_active()
    
    def get_path_by_id(self, path_id: int) -> Optional[Dict[str, Any]]:
        """Get path by ID"""
        return self.paths_repo.get_by_id(path_id)
    
    def create_path(self, data: Dict[str, Any], created_by: int = 1) -> Dict[str, Any]:
        """Create a new path"""
        data["created_by"] = created_by
        return self.paths_repo.create(data)
    
    def update_path(self, path_id: int, data: Dict[str, Any], updated_by: int = 1) -> Dict[str, Any]:
        """Update a path"""
        data["updated_by"] = updated_by
        return self.paths_repo.update(path_id, data)
    
    def delete_path(self, path_id: int, deleted_by: int = 1) -> Dict[str, Any]:
        """Soft delete a path"""
        return self.paths_repo.soft_delete(path_id, deleted_by)
    
    # Routes operations
    def get_routes(self) -> List[Dict[str, Any]]:
        """Get all active routes"""
        return self.routes_repo.get_all_active()
    
    def get_route_by_id(self, route_id: int) -> Optional[Dict[str, Any]]:
        """Get route by ID"""
        return self.routes_repo.get_by_id(route_id)
    
    def create_route(self, data: Dict[str, Any], created_by: int = 1) -> Dict[str, Any]:
        """Create a new route"""
        data["created_by"] = created_by
        # Convert time to string if needed
        if "shift_time" in data and hasattr(data["shift_time"], "strftime"):
            data["shift_time"] = data["shift_time"].strftime("%H:%M:%S")
        return self.routes_repo.create(data)
    
    def update_route(self, route_id: int, data: Dict[str, Any], updated_by: int = 1) -> Dict[str, Any]:
        """Update a route"""
        data["updated_by"] = updated_by
        # Convert time to string if needed
        if "shift_time" in data and hasattr(data["shift_time"], "strftime"):
            data["shift_time"] = data["shift_time"].strftime("%H:%M:%S")
        return self.routes_repo.update(route_id, data)
    
    def delete_route(self, route_id: int, deleted_by: int = 1) -> Dict[str, Any]:
        """Soft delete a route"""
        return self.routes_repo.soft_delete(route_id, deleted_by)
    
    # Vehicles operations
    def get_vehicles(self) -> List[Dict[str, Any]]:
        """Get all active vehicles"""
        return self.vehicles_repo.get_all_active()
    
    def get_vehicle_by_id(self, vehicle_id: int) -> Optional[Dict[str, Any]]:
        """Get vehicle by ID"""
        return self.vehicles_repo.get_by_id(vehicle_id)
    
    def create_vehicle(self, data: Dict[str, Any], created_by: int = 1) -> Dict[str, Any]:
        """Create a new vehicle"""
        data["created_by"] = created_by
        return self.vehicles_repo.create(data)
    
    def update_vehicle(self, vehicle_id: int, data: Dict[str, Any], updated_by: int = 1) -> Dict[str, Any]:
        """Update a vehicle"""
        data["updated_by"] = updated_by
        return self.vehicles_repo.update(vehicle_id, data)
    
    def delete_vehicle(self, vehicle_id: int, deleted_by: int = 1) -> Dict[str, Any]:
        """Soft delete a vehicle"""
        return self.vehicles_repo.soft_delete(vehicle_id, deleted_by)
    
    # Drivers operations
    def get_drivers(self) -> List[Dict[str, Any]]:
        """Get all active drivers"""
        return self.drivers_repo.get_all_active()
    
    def get_driver_by_id(self, driver_id: int) -> Optional[Dict[str, Any]]:
        """Get driver by ID"""
        return self.drivers_repo.get_by_id(driver_id)
    
    def create_driver(self, data: Dict[str, Any], created_by: int = 1) -> Dict[str, Any]:
        """Create a new driver"""
        data["created_by"] = created_by
        return self.drivers_repo.create(data)
    
    def update_driver(self, driver_id: int, data: Dict[str, Any], updated_by: int = 1) -> Dict[str, Any]:
        """Update a driver"""
        data["updated_by"] = updated_by
        return self.drivers_repo.update(driver_id, data)
    
    def delete_driver(self, driver_id: int, deleted_by: int = 1) -> Dict[str, Any]:
        """Soft delete a driver"""
        return self.drivers_repo.soft_delete(driver_id, deleted_by)
    
    # Trips operations
    def get_trips(self) -> List[Dict[str, Any]]:
        """Get all active trips"""
        return self.trips_repo.get_all_active()
    
    def get_trip_by_id(self, trip_id: int) -> Optional[Dict[str, Any]]:
        """Get trip by ID"""
        return self.trips_repo.get_by_id(trip_id)
    
    def create_trip(self, data: Dict[str, Any], created_by: int = 1) -> Dict[str, Any]:
        """Create a new trip"""
        data["created_by"] = created_by
        return self.trips_repo.create(data)
    
    def update_trip(self, trip_id: int, data: Dict[str, Any], updated_by: int = 1) -> Dict[str, Any]:
        """Update a trip"""
        data["updated_by"] = updated_by
        return self.trips_repo.update(trip_id, data)
    
    def delete_trip(self, trip_id: int, deleted_by: int = 1) -> Dict[str, Any]:
        """Soft delete a trip"""
        return self.trips_repo.soft_delete(trip_id, deleted_by)
    
    # Deployments operations
    def get_deployments(self) -> List[Dict[str, Any]]:
        """Get all active deployments"""
        return self.deployments_repo.get_all_active()
    
    def get_deployment_by_id(self, deployment_id: int) -> Optional[Dict[str, Any]]:
        """Get deployment by ID"""
        return self.deployments_repo.get_by_id(deployment_id)
    
    def get_deployment_by_trip(self, trip_id: int) -> Optional[Dict[str, Any]]:
        """Get deployment by trip ID"""
        deployments = self.deployments_repo.get_all_active()
        for deployment in deployments:
            if deployment.get("trip_id") == trip_id:
                return deployment
        return None
    
    def create_deployment(self, data: Dict[str, Any], created_by: int = 1) -> Dict[str, Any]:
        """Create a new deployment"""
        data["created_by"] = created_by
        return self.deployments_repo.create(data)
    
    def update_deployment(self, deployment_id: int, data: Dict[str, Any], updated_by: int = 1) -> Dict[str, Any]:
        """Update a deployment"""
        data["updated_by"] = updated_by
        return self.deployments_repo.update(deployment_id, data)
    
    def delete_deployment(self, deployment_id: int, deleted_by: int = 1) -> Dict[str, Any]:
        """Soft delete a deployment"""
        return self.deployments_repo.soft_delete(deployment_id, deleted_by)

