"""
Service layer for stops operations
"""

from typing import List, Dict, Any, Optional
from database import StopsRepository
from backend.models.schemas import StopCreate, StopUpdate


class StopsService:
    """Service for stops business logic"""
    
    def __init__(self):
        self.repository = StopsRepository()
    
    def get_all(self) -> List[Dict[str, Any]]:
        """Get all active stops"""
        return self.repository.get_all_active()
    
    def get_by_id(self, stop_id: int) -> Optional[Dict[str, Any]]:
        """Get stop by ID"""
        return self.repository.get_by_id(stop_id)
    
    def create(self, stop_data: StopCreate) -> Dict[str, Any]:
        """Create a new stop"""
        data = stop_data.model_dump(exclude_none=True)
        # Set default created_by if not provided
        if "created_by" not in data or data["created_by"] is None:
            data["created_by"] = 1  # Default to admin user
        # Validate and round coordinates
        if "latitude" in data and data["latitude"] is not None:
            lat = float(data["latitude"])
            if lat < -90 or lat > 90:
                raise ValueError("Latitude must be between -90 and 90")
            data["latitude"] = round(lat, 8)
        if "longitude" in data and data["longitude"] is not None:
            lng = float(data["longitude"])
            if lng < -180 or lng > 180:
                raise ValueError("Longitude must be between -180 and 180")
            data["longitude"] = round(lng, 8)
        return self.repository.create(data)
    
    def update(self, stop_id: int, stop_data: StopUpdate, updated_by: Optional[int] = None) -> Dict[str, Any]:
        """Update a stop - automatically persists to database"""
        data = stop_data.model_dump(exclude_none=True)
        # Automatically set updated_by if provided
        if updated_by is not None:
            data["updated_by"] = updated_by
        # Validate and round coordinates
        if "latitude" in data and data["latitude"] is not None:
            lat = float(data["latitude"])
            if lat < -90 or lat > 90:
                raise ValueError("Latitude must be between -90 and 90")
            data["latitude"] = round(lat, 8)
        if "longitude" in data and data["longitude"] is not None:
            lng = float(data["longitude"])
            if lng < -180 or lng > 180:
                raise ValueError("Longitude must be between -180 and 180")
            data["longitude"] = round(lng, 8)
        # Update in database (triggers will auto-update updated_at)
        result = self.repository.update(stop_id, data)
        # Verify update was successful by fetching updated record
        if result:
            return self.repository.get_by_id(stop_id) or result
        return result
    
    def soft_delete(self, stop_id: int, deleted_by: int) -> Dict[str, Any]:
        """Soft delete a stop"""
        return self.repository.soft_delete(stop_id, deleted_by)

