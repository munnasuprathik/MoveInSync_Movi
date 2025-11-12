"""
Service layer for paths operations
"""

from typing import List, Dict, Any, Optional
from database import PathsRepository
from backend.models.schemas import PathCreate, PathUpdate


class PathsService:
    """Service for paths business logic"""
    
    def __init__(self):
        self.repository = PathsRepository()
    
    def get_all(self) -> List[Dict[str, Any]]:
        """Get all active paths"""
        return self.repository.get_all_active()
    
    def get_by_id(self, path_id: int) -> Optional[Dict[str, Any]]:
        """Get path by ID"""
        return self.repository.get_by_id(path_id)
    
    def get_stops_for_path(self, path_id: int) -> List[Dict[str, Any]]:
        """Get all stops for a specific path"""
        path = self.repository.get_by_id(path_id)
        if not path:
            return []
        
        from database import StopsRepository
        stops_repo = StopsRepository()
        stop_ids = path.get("ordered_list_of_stop_ids", [])
        
        stops = []
        for stop_id in stop_ids:
            stop = stops_repo.get_by_id(stop_id)
            if stop:
                stops.append(stop)
        
        return stops
    
    def create(self, path_data: PathCreate) -> Dict[str, Any]:
        """Create a new path"""
        data = path_data.model_dump(exclude_none=True)
        return self.repository.create(data)
    
    def update(self, path_id: int, path_data: PathUpdate, updated_by: Optional[int] = None) -> Dict[str, Any]:
        """Update a path - automatically persists to database"""
        data = path_data.model_dump(exclude_none=True)
        if updated_by is not None:
            data["updated_by"] = updated_by
        result = self.repository.update(path_id, data)
        if result:
            return self.repository.get_by_id(path_id) or result
        return result
    
    def soft_delete(self, path_id: int, deleted_by: int) -> Dict[str, Any]:
        """Soft delete a path"""
        return self.repository.soft_delete(path_id, deleted_by)

