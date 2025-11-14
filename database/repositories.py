"""
Repository layer for database operations.

Provides data access methods for all database tables with proper
error handling and soft delete support.
"""

from typing import List, Dict, Any, Optional
from database.client import get_client


class BaseRepository:
    """Base repository with common database operations"""
    
    def __init__(self, table_name: str):
        self.table_name = table_name
        self.client = get_client()
    
    def get_all_active(self) -> List[Dict[str, Any]]:
        """Get all active (non-deleted) records, sorted by created_at descending (newest first)"""
        try:
            result = self.client.table(self.table_name).select("*").is_("deleted_at", None).order("created_at", desc=True).execute()
            if result.data is None:
                print(f"Warning: {self.table_name}.get_all_active() returned None data")
                return []
            return result.data
        except Exception as e:
            print(f"Error fetching {self.table_name} from Supabase: {str(e)}")
            raise Exception(f"Failed to fetch {self.table_name} from database: {str(e)}")
    
    def get_by_id(self, record_id: int) -> Optional[Dict[str, Any]]:
        """Get a single record by ID (only if not deleted)"""
        result = self.client.table(self.table_name).select("*").eq("id", record_id).is_("deleted_at", None).execute()
        return result.data[0] if result.data else None
    
    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new record"""
        result = self.client.table(self.table_name).insert(data).execute()
        return result.data[0] if result.data else {}
    
    def update(self, record_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing record"""
        result = self.client.table(self.table_name).update(data).eq("id", record_id).execute()
        return result.data[0] if result.data else {}
    
    def soft_delete(self, record_id: int, deleted_by: int) -> Dict[str, Any]:
        """Soft delete a record"""
        from datetime import datetime
        result = self.client.table(self.table_name).update({
            "deleted_at": datetime.now().isoformat(),
            "deleted_by": deleted_by
        }).eq("id", record_id).execute()
        return result.data[0] if result.data else {}


class StopsRepository(BaseRepository):
    """Repository for stops operations"""
    
    def __init__(self):
        super().__init__("stops")
    
    def get_by_id(self, stop_id: int) -> Optional[Dict[str, Any]]:
        """Get stop by ID"""
        result = self.client.table(self.table_name).select("*").eq("stop_id", stop_id).is_("deleted_at", None).execute()
        return result.data[0] if result.data else None
    
    def update(self, stop_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update stop"""
        result = self.client.table(self.table_name).update(data).eq("stop_id", stop_id).execute()
        return result.data[0] if result.data else {}
    
    def soft_delete(self, stop_id: int, deleted_by: int) -> Dict[str, Any]:
        """Soft delete stop"""
        from datetime import datetime
        result = self.client.table(self.table_name).update({
            "deleted_at": datetime.now().isoformat(),
            "deleted_by": deleted_by
        }).eq("stop_id", stop_id).execute()
        return result.data[0] if result.data else {}


class PathsRepository(BaseRepository):
    """Repository for paths operations"""
    
    def __init__(self):
        super().__init__("paths")
    
    def get_by_id(self, path_id: int) -> Optional[Dict[str, Any]]:
        """Get path by ID"""
        result = self.client.table(self.table_name).select("*").eq("path_id", path_id).is_("deleted_at", None).execute()
        return result.data[0] if result.data else None
    
    def update(self, path_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update path"""
        result = self.client.table(self.table_name).update(data).eq("path_id", path_id).execute()
        return result.data[0] if result.data else {}
    
    def soft_delete(self, path_id: int, deleted_by: int) -> Dict[str, Any]:
        """Soft delete path"""
        from datetime import datetime
        result = self.client.table(self.table_name).update({
            "deleted_at": datetime.now().isoformat(),
            "deleted_by": deleted_by
        }).eq("path_id", path_id).execute()
        return result.data[0] if result.data else {}


class RoutesRepository(BaseRepository):
    """Repository for routes operations"""
    
    def __init__(self):
        super().__init__("routes")
    
    def get_by_id(self, route_id: int) -> Optional[Dict[str, Any]]:
        """Get route by ID"""
        result = self.client.table(self.table_name).select("*").eq("route_id", route_id).is_("deleted_at", None).execute()
        return result.data[0] if result.data else None
    
    def update(self, route_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update route"""
        result = self.client.table(self.table_name).update(data).eq("route_id", route_id).execute()
        return result.data[0] if result.data else {}
    
    def soft_delete(self, route_id: int, deleted_by: int) -> Dict[str, Any]:
        """Soft delete route"""
        from datetime import datetime
        result = self.client.table(self.table_name).update({
            "deleted_at": datetime.now().isoformat(),
            "deleted_by": deleted_by
        }).eq("route_id", route_id).execute()
        return result.data[0] if result.data else {}


class VehiclesRepository(BaseRepository):
    """Repository for vehicles operations"""
    
    def __init__(self):
        super().__init__("vehicles")
    
    def get_by_id(self, vehicle_id: int) -> Optional[Dict[str, Any]]:
        """Get vehicle by ID"""
        result = self.client.table(self.table_name).select("*").eq("vehicle_id", vehicle_id).is_("deleted_at", None).execute()
        return result.data[0] if result.data else None
    
    def update(self, vehicle_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update vehicle"""
        result = self.client.table(self.table_name).update(data).eq("vehicle_id", vehicle_id).execute()
        return result.data[0] if result.data else {}
    
    def soft_delete(self, vehicle_id: int, deleted_by: int) -> Dict[str, Any]:
        """Soft delete vehicle"""
        from datetime import datetime
        result = self.client.table(self.table_name).update({
            "deleted_at": datetime.now().isoformat(),
            "deleted_by": deleted_by
        }).eq("vehicle_id", vehicle_id).execute()
        return result.data[0] if result.data else {}


class DriversRepository(BaseRepository):
    """Repository for drivers operations"""
    
    def __init__(self):
        super().__init__("drivers")
    
    def get_by_id(self, driver_id: int) -> Optional[Dict[str, Any]]:
        """Get driver by ID"""
        result = self.client.table(self.table_name).select("*").eq("driver_id", driver_id).is_("deleted_at", None).execute()
        return result.data[0] if result.data else None
    
    def update(self, driver_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update driver"""
        result = self.client.table(self.table_name).update(data).eq("driver_id", driver_id).execute()
        return result.data[0] if result.data else {}
    
    def soft_delete(self, driver_id: int, deleted_by: int) -> Dict[str, Any]:
        """Soft delete driver"""
        from datetime import datetime
        result = self.client.table(self.table_name).update({
            "deleted_at": datetime.now().isoformat(),
            "deleted_by": deleted_by
        }).eq("driver_id", driver_id).execute()
        return result.data[0] if result.data else {}


class TripsRepository(BaseRepository):
    """Repository for daily trips operations"""
    
    def __init__(self):
        super().__init__("daily_trips")
    
    def get_by_id(self, trip_id: int) -> Optional[Dict[str, Any]]:
        """Get trip by ID"""
        result = self.client.table(self.table_name).select("*").eq("trip_id", trip_id).is_("deleted_at", None).execute()
        return result.data[0] if result.data else None
    
    def update(self, trip_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update trip"""
        result = self.client.table(self.table_name).update(data).eq("trip_id", trip_id).execute()
        return result.data[0] if result.data else {}
    
    def soft_delete(self, trip_id: int, deleted_by: int) -> Dict[str, Any]:
        """Soft delete trip"""
        from datetime import datetime
        result = self.client.table(self.table_name).update({
            "deleted_at": datetime.now().isoformat(),
            "deleted_by": deleted_by
        }).eq("trip_id", trip_id).execute()
        return result.data[0] if result.data else {}


class DeploymentsRepository(BaseRepository):
    """Repository for deployments operations"""
    
    def __init__(self):
        super().__init__("deployments")
    
    def get_by_id(self, deployment_id: int) -> Optional[Dict[str, Any]]:
        """Get deployment by ID"""
        result = self.client.table(self.table_name).select("*").eq("deployment_id", deployment_id).is_("deleted_at", None).execute()
        return result.data[0] if result.data else None
    
    def update(self, deployment_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update deployment"""
        result = self.client.table(self.table_name).update(data).eq("deployment_id", deployment_id).execute()
        return result.data[0] if result.data else {}
    
    def soft_delete(self, deployment_id: int, deleted_by: int) -> Dict[str, Any]:
        """Soft delete deployment"""
        from datetime import datetime
        result = self.client.table(self.table_name).update({
            "deleted_at": datetime.now().isoformat(),
            "deleted_by": deleted_by
        }).eq("deployment_id", deployment_id).execute()
        return result.data[0] if result.data else {}

