"""
Service layer for routes operations
"""

from typing import List, Dict, Any, Optional
from datetime import time
from database import RoutesRepository
from backend.models.schemas import RouteCreate, RouteUpdate


class RoutesService:
    """Service for routes business logic"""
    
    def __init__(self):
        self.repository = RoutesRepository()
    
    def get_all(self) -> List[Dict[str, Any]]:
        """Get all active routes"""
        return self.repository.get_all_active()
    
    def get_by_id(self, route_id: int) -> Optional[Dict[str, Any]]:
        """Get route by ID"""
        return self.repository.get_by_id(route_id)
    
    def get_routes_by_path(self, path_id: int) -> List[Dict[str, Any]]:
        """Get all routes that use a specific path"""
        all_routes = self.repository.get_all_active()
        return [route for route in all_routes if route.get("path_id") == path_id]
    
    def _convert_time_to_string(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert time objects to strings for JSON serialization"""
        if "shift_time" in data and isinstance(data["shift_time"], time):
            data["shift_time"] = data["shift_time"].strftime("%H:%M:%S")
        return data
    
    def create(self, route_data: RouteCreate) -> Dict[str, Any]:
        """Create a new route"""
        data = route_data.model_dump(exclude_none=True)
        # Set default created_by if not provided
        if "created_by" not in data or data["created_by"] is None:
            data["created_by"] = 1  # Default to admin user
        # Convert time objects to strings
        data = self._convert_time_to_string(data)
        return self.repository.create(data)
    
    def update(self, route_id: int, route_data: RouteUpdate, updated_by: Optional[int] = None) -> Dict[str, Any]:
        """Update a route - automatically persists to database"""
        data = route_data.model_dump(exclude_none=True)
        # Automatically set updated_by if provided
        if updated_by is not None:
            data["updated_by"] = updated_by
        # Convert time objects to strings
        data = self._convert_time_to_string(data)
        result = self.repository.update(route_id, data)
        if result:
            return self.repository.get_by_id(route_id) or result
        return result
    
    def soft_delete(self, route_id: int, deleted_by: int) -> Dict[str, Any]:
        """Soft delete a route"""
        return self.repository.soft_delete(route_id, deleted_by)

