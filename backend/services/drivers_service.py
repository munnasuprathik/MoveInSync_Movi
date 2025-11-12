"""
Service layer for drivers operations
"""

from typing import List, Dict, Any, Optional
from database import DriversRepository
from backend.models.schemas import DriverCreate, DriverUpdate


class DriversService:
    """Service for drivers business logic"""
    
    def __init__(self):
        self.repository = DriversRepository()
    
    def get_all(self) -> List[Dict[str, Any]]:
        """Get all active drivers"""
        return self.repository.get_all_active()
    
    def get_by_id(self, driver_id: int) -> Optional[Dict[str, Any]]:
        """Get driver by ID"""
        return self.repository.get_by_id(driver_id)
    
    def create(self, driver_data: DriverCreate) -> Dict[str, Any]:
        """Create a new driver"""
        data = driver_data.model_dump(exclude_none=True)
        return self.repository.create(data)
    
    def update(self, driver_id: int, driver_data: DriverUpdate, updated_by: Optional[int] = None) -> Dict[str, Any]:
        """Update a driver - automatically persists to database"""
        data = driver_data.model_dump(exclude_none=True)
        if updated_by is not None:
            data["updated_by"] = updated_by
        result = self.repository.update(driver_id, data)
        if result:
            return self.repository.get_by_id(driver_id) or result
        return result
    
    def soft_delete(self, driver_id: int, deleted_by: int) -> Dict[str, Any]:
        """Soft delete a driver"""
        return self.repository.soft_delete(driver_id, deleted_by)

