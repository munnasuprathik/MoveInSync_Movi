"""
Service layer for deployments operations
"""

from typing import List, Dict, Any, Optional
from database import DeploymentsRepository
from backend.models.schemas import DeploymentCreate, DeploymentUpdate


class DeploymentsService:
    """Service for deployments business logic"""
    
    def __init__(self):
        self.repository = DeploymentsRepository()
    
    def get_all(self) -> List[Dict[str, Any]]:
        """Get all active deployments"""
        return self.repository.get_all_active()
    
    def get_by_id(self, deployment_id: int) -> Optional[Dict[str, Any]]:
        """Get deployment by ID"""
        return self.repository.get_by_id(deployment_id)
    
    def get_by_trip_id(self, trip_id: int) -> Optional[Dict[str, Any]]:
        """Get deployment for a specific trip"""
        all_deployments = self.repository.get_all_active()
        for deployment in all_deployments:
            if deployment.get("trip_id") == trip_id:
                return deployment
        return None
    
    def create(self, deployment_data: DeploymentCreate) -> Dict[str, Any]:
        """Create a new deployment"""
        data = deployment_data.model_dump(exclude_none=True)
        return self.repository.create(data)
    
    def update(self, deployment_id: int, deployment_data: DeploymentUpdate, updated_by: Optional[int] = None) -> Dict[str, Any]:
        """Update a deployment - automatically persists to database"""
        data = deployment_data.model_dump(exclude_none=True)
        if updated_by is not None:
            data["updated_by"] = updated_by
        result = self.repository.update(deployment_id, data)
        if result:
            return self.repository.get_by_id(deployment_id) or result
        return result
    
    def soft_delete(self, deployment_id: int, deleted_by: int) -> Dict[str, Any]:
        """Soft delete a deployment"""
        return self.repository.soft_delete(deployment_id, deleted_by)
    
    def remove_by_trip(self, trip_id: int, deleted_by: int) -> Dict[str, Any]:
        """Remove deployment for a trip"""
        deployment = self.get_by_trip_id(trip_id)
        if deployment:
            return self.repository.soft_delete(deployment.get("deployment_id"), deleted_by)
        return {}

