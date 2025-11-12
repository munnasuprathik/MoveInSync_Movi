"""
Service layer for vehicles operations
"""

from typing import List, Dict, Any, Optional
from database import VehiclesRepository
from backend.models.schemas import VehicleCreate, VehicleUpdate


class VehiclesService:
    """Service for vehicles business logic"""
    
    def __init__(self):
        self.repository = VehiclesRepository()
    
    def get_all(self) -> List[Dict[str, Any]]:
        """Get all active vehicles"""
        return self.repository.get_all_active()
    
    def get_by_id(self, vehicle_id: int) -> Optional[Dict[str, Any]]:
        """Get vehicle by ID"""
        return self.repository.get_by_id(vehicle_id)
    
    def get_unassigned_vehicles(self) -> List[Dict[str, Any]]:
        """Get vehicles that are not assigned to any trip"""
        from database import get_client
        client = get_client()
        
        # Get all active vehicles
        all_vehicles = self.repository.get_all_active()
        
        # Get all active deployments
        deployments = client.table("deployments").select("vehicle_id").is_("deleted_at", "null").execute()
        assigned_vehicle_ids = {dep.get("vehicle_id") for dep in (deployments.data or [])}
        
        # Filter out assigned vehicles
        unassigned = [v for v in all_vehicles if v.get("vehicle_id") not in assigned_vehicle_ids]
        return unassigned
    
    def create(self, vehicle_data: VehicleCreate) -> Dict[str, Any]:
        """Create a new vehicle"""
        data = vehicle_data.model_dump(exclude_none=True)
        return self.repository.create(data)
    
    def update(self, vehicle_id: int, vehicle_data: VehicleUpdate, updated_by: Optional[int] = None) -> Dict[str, Any]:
        """Update a vehicle - automatically persists to database"""
        data = vehicle_data.model_dump(exclude_none=True)
        if updated_by is not None:
            data["updated_by"] = updated_by
        result = self.repository.update(vehicle_id, data)
        if result:
            return self.repository.get_by_id(vehicle_id) or result
        return result
    
    def soft_delete(self, vehicle_id: int, deleted_by: int) -> Dict[str, Any]:
        """Soft delete a vehicle"""
        return self.repository.soft_delete(vehicle_id, deleted_by)

