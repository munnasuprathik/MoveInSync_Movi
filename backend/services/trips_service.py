"""
Service layer for trips operations
"""

from typing import List, Dict, Any, Optional
from database import TripsRepository
from backend.models.schemas import TripCreate, TripUpdate


class TripsService:
    """Service for trips business logic"""
    
    def __init__(self):
        self.repository = TripsRepository()
    
    def get_all(self) -> List[Dict[str, Any]]:
        """Get all active trips"""
        return self.repository.get_all_active()
    
    def get_by_id(self, trip_id: int) -> Optional[Dict[str, Any]]:
        """Get trip by ID"""
        return self.repository.get_by_id(trip_id)
    
    def get_by_display_name(self, display_name: str) -> Optional[Dict[str, Any]]:
        """Get trip by display name"""
        all_trips = self.repository.get_all_active()
        for trip in all_trips:
            if trip.get("display_name") == display_name:
                return trip
        return None
    
    def create(self, trip_data: TripCreate) -> Dict[str, Any]:
        """Create a new trip"""
        data = trip_data.model_dump(exclude_none=True)
        return self.repository.create(data)
    
    def update(self, trip_id: int, trip_data: TripUpdate, updated_by: Optional[int] = None) -> Dict[str, Any]:
        """Update a trip - automatically persists to database"""
        data = trip_data.model_dump(exclude_none=True)
        if updated_by is not None:
            data["updated_by"] = updated_by
        result = self.repository.update(trip_id, data)
        if result:
            return self.repository.get_by_id(trip_id) or result
        return result
    
    def soft_delete(self, trip_id: int, deleted_by: int) -> Dict[str, Any]:
        """Soft delete a trip"""
        return self.repository.soft_delete(trip_id, deleted_by)

