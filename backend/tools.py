"""
Tool functions for wrapping repository operations.
Provides high-level functions for common transport management operations.
"""

from typing import Dict, Any, List, Optional, Union
from database.client import get_client
from database.repositories import (
    StopsRepository,
    PathsRepository,
    RoutesRepository,
    VehiclesRepository,
    DriversRepository,
    TripsRepository,
    DeploymentsRepository
)

MAX_RESULTS = 50


def _limit_results(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Return result metadata. If the dataset is large, keep all rows but flag it
    so the caller can mention the volume and suggest filters.
    """
    if len(records) > MAX_RESULTS:
        return {
            "data": records,
            "limited": True,
            "total": len(records)
        }
    return {"data": records, "limited": False, "total": len(records)}


def _success(data: Any, message: str) -> Dict[str, Any]:
    return {"success": True, "data": data, "message": message}


def _error(message: str, error: str = "") -> Dict[str, Any]:
    return {"success": False, "data": None, "message": message, "error": error}



# ================================================================
# VEHICLE TOOLS
# ================================================================

def get_all_vehicles() -> Dict[str, Any]:
    """Get all active vehicles."""
    try:
        repo = VehiclesRepository()
        vehicles = repo.get_all_active()
        limited = _limit_results(vehicles)
        message = f"Found {limited['total']} active vehicles."
        if limited["limited"]:
            message += " Large dataset detected; consider applying filters for a more focused list."
        return _success(limited["data"], message)
    except Exception as e:
        return _error("Failed to fetch vehicles", str(e))


def get_vehicle_by_id(vehicle_id: int) -> Dict[str, Any]:
    """Get vehicle details by vehicle_id."""
    try:
        repo = VehiclesRepository()
        vehicle = repo.get_by_id(vehicle_id)
        if not vehicle:
            return _error(f"Vehicle {vehicle_id} not found", "Vehicle not found")
        return _success(vehicle, f"Vehicle {vehicle_id} found")
    except Exception as e:
        return _error("Failed to fetch vehicle", str(e))


def create_vehicle(vehicle_data: Dict[str, Any], created_by: int = 1) -> Dict[str, Any]:
    """Create a new vehicle record."""
    try:
        required_fields = ["license_plate", "type", "capacity"]
        for field in required_fields:
            if not vehicle_data.get(field):
                return _error(f"Field '{field}' is required", "Validation error")

        vehicle_data = vehicle_data.copy()
        vehicle_data["created_by"] = created_by
        vehicle_data["capacity"] = int(vehicle_data["capacity"])
        if "year" in vehicle_data and vehicle_data["year"] not in (None, ""):
            vehicle_data["year"] = int(vehicle_data["year"])

        repo = VehiclesRepository()
        existing = repo.get_all_active()
        license_plate = vehicle_data["license_plate"].strip().lower()
        if any((v.get("license_plate") or "").strip().lower() == license_plate for v in existing):
            return _error(
                f"Vehicle with license plate '{vehicle_data['license_plate']}' already exists",
                "Duplicate license plate"
            )

        vehicle = repo.create(vehicle_data)
        return _success(vehicle, f"Vehicle '{vehicle.get('license_plate')}' created successfully")
    except ValueError as ve:
        return _error("Invalid numeric value provided", str(ve))
    except Exception as e:
        return _error("Failed to create vehicle", str(e))


def update_vehicle(vehicle_id: int, update_data: Dict[str, Any], updated_by: int = 1) -> Dict[str, Any]:
    """Update vehicle details."""
    try:
        if not update_data:
            return _error("No update fields provided", "Validation error")

        repo = VehiclesRepository()
        existing = repo.get_by_id(vehicle_id)
        if not existing:
            return _error(f"Vehicle {vehicle_id} not found", "Vehicle not found")

        data = update_data.copy()
        data["updated_by"] = updated_by
        if "capacity" in data and data["capacity"] not in (None, ""):
            data["capacity"] = int(data["capacity"])
        if "year" in data and data["year"] not in (None, ""):
            data["year"] = int(data["year"])

        updated = repo.update(vehicle_id, data)
        return _success(updated or {**existing, **data}, f"Vehicle {vehicle_id} updated successfully")
    except ValueError as ve:
        return _error("Invalid numeric value provided", str(ve))
    except Exception as e:
        return _error("Failed to update vehicle", str(e))


def delete_vehicle(vehicle_id: int, deleted_by: int = 1) -> Dict[str, Any]:
    """Soft delete a vehicle."""
    try:
        repo = VehiclesRepository()
        existing = repo.get_by_id(vehicle_id)
        if not existing:
            return _error(f"Vehicle {vehicle_id} not found", "Vehicle not found")
        deleted = repo.soft_delete(vehicle_id, deleted_by)
        return _success(deleted or {"vehicle_id": vehicle_id}, f"Vehicle {vehicle_id} deleted successfully")
    except Exception as e:
        return _error("Failed to delete vehicle", str(e))


def filter_vehicles_by_type(vehicle_type: str) -> Dict[str, Any]:
    """Filter vehicles by type (e.g., Bus, Cab)."""
    try:
        repo = VehiclesRepository()
        vehicles = repo.get_all_active()
        filtered = [v for v in vehicles if (v.get("type") or "").lower() == vehicle_type.lower()]
        limited = _limit_results(filtered)
        message = f"Found {limited['total']} vehicles of type '{vehicle_type}'."
        if limited["limited"]:
            message += " Large dataset detected; consider applying filters for a more focused list."
        return _success(limited["data"], message)
    except Exception as e:
        return _error("Failed to filter vehicles", str(e))


def filter_vehicles_by_availability(is_available: bool) -> Dict[str, Any]:
    """Filter vehicles by availability status."""
    try:
        repo = VehiclesRepository()
        vehicles = repo.get_all_active()
        filtered = [v for v in vehicles if bool(v.get("is_available", False)) == is_available]
        limited = _limit_results(filtered)
        status = "available" if is_available else "unavailable"
        message = f"Found {limited['total']} {status} vehicles."
        if limited["limited"]:
            message += " Large dataset detected; consider applying filters for a more focused list."
        return _success(limited["data"], message)
    except Exception as e:
        return _error("Failed to filter vehicles", str(e))




# ================================================================
# DEPLOYMENT TOOLS
# ================================================================

def get_all_deployments() -> Dict[str, Any]:
    """Get all active deployments."""
    try:
        repo = DeploymentsRepository()
        deployments = repo.get_all_active()
        limited = _limit_results(deployments)
        message = f"Found {limited['total']} active deployments."
        if limited["limited"]:
            message += " Large dataset detected; consider applying filters for a more focused list."
        return _success(limited["data"], message)
    except Exception as e:
        return _error("Failed to fetch deployments", str(e))


def get_deployment_by_id(deployment_id: int) -> Dict[str, Any]:
    """Get deployment details by deployment_id."""
    try:
        repo = DeploymentsRepository()
        deployment = repo.get_by_id(deployment_id)
        if not deployment:
            return _error(f"Deployment {deployment_id} not found", "Deployment not found")
        return _success(deployment, f"Deployment {deployment_id} found")
    except Exception as e:
        return _error("Failed to fetch deployment", str(e))


def create_deployment(deployment_data: Dict[str, Any], created_by: int = 1) -> Dict[str, Any]:
    """Create a new deployment linking trip, vehicle, and driver."""
    try:
        required_fields = ["trip_id", "vehicle_id", "driver_id"]
        for field in required_fields:
            if not deployment_data.get(field):
                return _error(f"Field '{field}' is required", "Validation error")
        payload = deployment_data.copy()
        payload["trip_id"] = int(payload["trip_id"])
        payload["vehicle_id"] = int(payload["vehicle_id"])
        payload["driver_id"] = int(payload["driver_id"])
        payload["created_by"] = created_by
        repo = DeploymentsRepository()
        deployment = repo.create(payload)
        return _success(deployment, "Deployment created successfully")
    except ValueError as ve:
        return _error("Invalid numeric value provided", str(ve))
    except Exception as e:
        return _error("Failed to create deployment", str(e))


def delete_deployment(deployment_id: int, deleted_by: int = 1) -> Dict[str, Any]:
    """Soft delete a deployment."""
    try:
        repo = DeploymentsRepository()
        existing = repo.get_by_id(deployment_id)
        if not existing:
            return _error(f"Deployment {deployment_id} not found", "Deployment not found")
        deleted = repo.soft_delete(deployment_id, deleted_by)
        return _success(deleted or {"deployment_id": deployment_id}, f"Deployment {deployment_id} deleted successfully")
    except Exception as e:
        return _error("Failed to delete deployment", str(e))


def filter_deployments_by_trip(trip_id: int) -> Dict[str, Any]:
    """Get deployments associated with a specific trip."""
    try:
        repo = DeploymentsRepository()
        deployments = repo.get_all_active()
        filtered = [d for d in deployments if d.get("trip_id") == trip_id]
        limited = _limit_results(filtered)
        message = f"Found {limited['total']} deployments for trip {trip_id}."
        if limited["limited"]:
            message += " Large dataset detected; consider applying filters for a more focused list."
        return _success(limited["data"], message)
    except Exception as e:
        return _error("Failed to filter deployments", str(e))


def filter_deployments_by_vehicle(vehicle_id: int) -> Dict[str, Any]:
    """Get deployments associated with a specific vehicle."""
    try:
        repo = DeploymentsRepository()
        deployments = repo.get_all_active()
        filtered = [d for d in deployments if d.get("vehicle_id") == vehicle_id]
        limited = _limit_results(filtered)
        message = f"Found {limited['total']} deployments for vehicle {vehicle_id}."
        if limited["limited"]:
            message += " Large dataset detected; consider applying filters for a more focused list."
        return _success(limited["data"], message)
    except Exception as e:
        return _error("Failed to filter deployments", str(e))


def filter_deployments_by_driver(driver_id: int) -> Dict[str, Any]:
    """Get deployments associated with a specific driver."""
    try:
        repo = DeploymentsRepository()
        deployments = repo.get_all_active()
        filtered = [d for d in deployments if d.get("driver_id") == driver_id]
        limited = _limit_results(filtered)
        message = f"Found {limited['total']} deployments for driver {driver_id}."
        if limited["limited"]:
            message += " Large dataset detected; consider applying filters for a more focused list."
        return _success(limited["data"], message)
    except Exception as e:
        return _error("Failed to filter deployments", str(e))




def get_unassigned_vehicles() -> Dict[str, Any]:
    """
    Get all vehicles that are not currently assigned to any active deployment.
    
    Returns:
        Dict with success status, data (list of vehicles), message, and optional error.
    """
    try:
        client = get_client()
        vehicles_repo = VehiclesRepository()
        deployments_repo = DeploymentsRepository()
        
        # Get all active vehicles
        all_vehicles = vehicles_repo.get_all_active()
        
        # Get all active deployments to find assigned vehicle IDs
        all_deployments = deployments_repo.get_all_active()
        assigned_vehicle_ids = {dep.get("vehicle_id") for dep in all_deployments if dep.get("vehicle_id")}
        
        # Filter out assigned vehicles
        unassigned_vehicles = [
            vehicle for vehicle in all_vehicles 
            if vehicle.get("vehicle_id") not in assigned_vehicle_ids
        ]
        
        return {
            "success": True,
            "data": unassigned_vehicles,
            "message": f"Found {len(unassigned_vehicles)} unassigned vehicles"
        }
    except Exception as e:
        return {
            "success": False,
            "data": [],
            "message": "Failed to get unassigned vehicles",
            "error": str(e)
        }


# ================================================================
# DRIVER TOOLS
# ================================================================

def get_all_drivers() -> Dict[str, Any]:
    """Get all active drivers."""
    try:
        repo = DriversRepository()
        drivers = repo.get_all_active()
        limited = _limit_results(drivers)
        message = f"Found {limited['total']} active drivers."
        if limited["limited"]:
            message += " Large dataset detected; consider applying filters for a more focused list."
        return _success(limited["data"], message)
    except Exception as e:
        return _error("Failed to fetch drivers", str(e))


def get_driver_by_id(driver_id: int) -> Dict[str, Any]:
    """Get driver details by driver_id."""
    try:
        repo = DriversRepository()
        driver = repo.get_by_id(driver_id)
        if not driver:
            return _error(f"Driver {driver_id} not found", "Driver not found")
        return _success(driver, f"Driver {driver_id} found")
    except Exception as e:
        return _error("Failed to fetch driver", str(e))


def create_driver(driver_data: Dict[str, Any], created_by: int = 1) -> Dict[str, Any]:
    """Create a new driver."""
    try:
        required_fields = ["name", "phone_number"]
        for field in required_fields:
            if not driver_data.get(field):
                return _error(f"Field '{field}' is required", "Validation error")

        repo = DriversRepository()
        payload = driver_data.copy()
        payload["created_by"] = created_by
        driver = repo.create(payload)
        return _success(driver, f"Driver '{driver.get('name')}' created successfully")
    except Exception as e:
        return _error("Failed to create driver", str(e))


def update_driver(driver_id: int, update_data: Dict[str, Any], updated_by: int = 1) -> Dict[str, Any]:
    """Update driver information."""
    try:
        if not update_data:
            return _error("No update fields provided", "Validation error")
        repo = DriversRepository()
        existing = repo.get_by_id(driver_id)
        if not existing:
            return _error(f"Driver {driver_id} not found", "Driver not found")
        payload = update_data.copy()
        payload["updated_by"] = updated_by
        updated = repo.update(driver_id, payload)
        return _success(updated or {**existing, **payload}, f"Driver {driver_id} updated successfully")
    except Exception as e:
        return _error("Failed to update driver", str(e))


def delete_driver(driver_id: int, deleted_by: int = 1) -> Dict[str, Any]:
    """Soft delete a driver."""
    try:
        repo = DriversRepository()
        existing = repo.get_by_id(driver_id)
        if not existing:
            return _error(f"Driver {driver_id} not found", "Driver not found")
        deleted = repo.soft_delete(driver_id, deleted_by)
        return _success(deleted or {"driver_id": driver_id}, f"Driver {driver_id} deleted successfully")
    except Exception as e:
        return _error("Failed to delete driver", str(e))


def filter_drivers_by_availability(is_available: bool) -> Dict[str, Any]:
    """Filter drivers by availability flag."""
    try:
        repo = DriversRepository()
        drivers = repo.get_all_active()
        filtered = [d for d in drivers if bool(d.get("is_available", False)) == is_available]
        limited = _limit_results(filtered)
        status = "available" if is_available else "unavailable"
        message = f"Found {limited['total']} {status} drivers."
        if limited["limited"]:
            message += " Large dataset detected; consider applying filters for a more focused list."
        return _success(limited["data"], message)
    except Exception as e:
        return _error("Failed to filter drivers", str(e))


# ================================================================
# STOP TOOLS
# ================================================================

def get_all_stops() -> Dict[str, Any]:
    """List all active stops."""
    try:
        repo = StopsRepository()
        stops = repo.get_all_active()
        limited = _limit_results(stops)
        message = f"Found {limited['total']} active stops."
        if limited["limited"]:
            message += " Large dataset detected; consider applying filters for a more focused list."
        return _success(limited["data"], message)
    except Exception as e:
        return _error("Failed to fetch stops", str(e))


def get_stop_by_id(stop_id: int) -> Dict[str, Any]:
    """Get stop details by ID."""
    try:
        repo = StopsRepository()
        stop = repo.get_by_id(stop_id)
        if not stop:
            return _error(f"Stop {stop_id} not found", "Stop not found")
        return _success(stop, f"Stop {stop_id} found")
    except Exception as e:
        return _error("Failed to fetch stop", str(e))


def create_stop_record(stop_data: Dict[str, Any], created_by: int = 1) -> Dict[str, Any]:
    """Create a new stop using structured data."""
    try:
        required_fields = ["name", "latitude", "longitude"]
        for field in required_fields:
            if stop_data.get(field) in (None, ""):
                return _error(f"Field '{field}' is required", "Validation error")
        name = str(stop_data["name"]).strip()
        latitude = float(stop_data["latitude"])
        longitude = float(stop_data["longitude"])
        description = stop_data.get("description")
        address = stop_data.get("address")
        return create_stop(name, latitude, longitude, description, address, created_by=created_by)
    except ValueError as ve:
        return _error("Invalid numeric value provided", str(ve))
    except Exception as e:
        return _error("Failed to create stop", str(e))


def update_stop(stop_id: int, update_data: Dict[str, Any], updated_by: int = 1) -> Dict[str, Any]:
    """Update stop details."""
    try:
        if not update_data:
            return _error("No update fields provided", "Validation error")
        repo = StopsRepository()
        existing = repo.get_by_id(stop_id)
        if not existing:
            return _error(f"Stop {stop_id} not found", "Stop not found")
        data = update_data.copy()
        if "latitude" in data and data["latitude"] not in (None, ""):
            data["latitude"] = float(data["latitude"])
        if "longitude" in data and data["longitude"] not in (None, ""):
            data["longitude"] = float(data["longitude"])
        data["updated_by"] = updated_by
        updated = repo.update(stop_id, data)
        return _success(updated or {**existing, **data}, f"Stop {stop_id} updated successfully")
    except ValueError as ve:
        return _error("Invalid numeric value provided", str(ve))
    except Exception as e:
        return _error("Failed to update stop", str(e))


def delete_stop(stop_id: int, deleted_by: int = 1) -> Dict[str, Any]:
    """Soft delete a stop."""
    try:
        repo = StopsRepository()
        existing = repo.get_by_id(stop_id)
        if not existing:
            return _error(f"Stop {stop_id} not found", "Stop not found")
        deleted = repo.soft_delete(stop_id, deleted_by)
        return _success(deleted or {"stop_id": stop_id}, f"Stop {stop_id} deleted successfully")
    except Exception as e:
        return _error("Failed to delete stop", str(e))


def search_stops_by_name(query: str) -> Dict[str, Any]:
    """Search stops by partial name match."""
    try:
        repo = StopsRepository()
        stops = repo.get_all_active()
        query_lower = query.lower()
        filtered = [s for s in stops if query_lower in (s.get("name") or "").lower()]
        limited = _limit_results(filtered)
        message = f"Found {limited['total']} stops matching '{query}'."
        if limited["limited"]:
            message += " Large dataset detected; consider applying filters for a more focused list."
        return _success(limited["data"], message)
    except Exception as e:
        return _error("Failed to search stops", str(e))


# ================================================================
# ROUTE TOOLS
# ================================================================

def get_all_routes() -> Dict[str, Any]:
    """List all active routes."""
    try:
        repo = RoutesRepository()
        routes = repo.get_all_active()
        limited = _limit_results(routes)
        message = f"Found {limited['total']} active routes."
        if limited["limited"]:
            message += " Large dataset detected; consider applying filters for a more focused list."
        return _success(limited["data"], message)
    except Exception as e:
        return _error("Failed to fetch routes", str(e))


def get_route_by_id(route_id: int) -> Dict[str, Any]:
    """Get route details by ID."""
    try:
        repo = RoutesRepository()
        route = repo.get_by_id(route_id)
        if not route:
            return _error(f"Route {route_id} not found", "Route not found")
        return _success(route, f"Route {route_id} found")
    except Exception as e:
        return _error("Failed to fetch route", str(e))


def create_route_record(route_data: Dict[str, Any], created_by: int = 1) -> Dict[str, Any]:
    """Create a new route."""
    try:
        required_fields = ["path_id", "shift_time", "direction", "route_display_name"]
        for field in required_fields:
            if route_data.get(field) in (None, ""):
                return _error(f"Field '{field}' is required", "Validation error")
        direction = route_data.get("direction", "Forward")
        status = route_data.get("status", "active")
        return create_route(
            path_id=str(route_data["path_id"]),
            shift_time=str(route_data["shift_time"]),
            direction=direction,
            route_display_name=str(route_data["route_display_name"]),
            start_point=route_data.get("start_point"),
            end_point=route_data.get("end_point"),
            status=status,
            notes=route_data.get("notes"),
            created_by=created_by,
        )
    except Exception as e:
        return _error("Failed to create route", str(e))


def update_route(route_id: int, update_data: Dict[str, Any], updated_by: int = 1) -> Dict[str, Any]:
    """Update route fields."""
    try:
        if not update_data:
            return _error("No update fields provided", "Validation error")
        repo = RoutesRepository()
        existing = repo.get_by_id(route_id)
        if not existing:
            return _error(f"Route {route_id} not found", "Route not found")
        data = update_data.copy()
        if "path_id" in data and data["path_id"] not in (None, ""):
            data["path_id"] = int(data["path_id"])
        if "shift_time" in data and data["shift_time"]:
            shift_time = str(data["shift_time"])
            if len(shift_time.split(":")) == 2:
                shift_time += ":00"
            data["shift_time"] = shift_time
        data["updated_by"] = updated_by
        updated = repo.update(route_id, data)
        return _success(updated or {**existing, **data}, f"Route {route_id} updated successfully")
    except ValueError as ve:
        return _error("Invalid numeric value provided", str(ve))
    except Exception as e:
        return _error("Failed to update route", str(e))


def delete_route(route_id: int, deleted_by: int = 1) -> Dict[str, Any]:
    """Soft delete a route."""
    try:
        repo = RoutesRepository()
        existing = repo.get_by_id(route_id)
        if not existing:
            return _error(f"Route {route_id} not found", "Route not found")
        deleted = repo.soft_delete(route_id, deleted_by)
        return _success(deleted or {"route_id": route_id}, f"Route {route_id} deleted successfully")
    except Exception as e:
        return _error("Failed to delete route", str(e))


def filter_routes_by_path(path_id: int) -> Dict[str, Any]:
    """Filter routes by path."""
    try:
        repo = RoutesRepository()
        routes = repo.get_all_active()
        filtered = [r for r in routes if r.get("path_id") == path_id]
        limited = _limit_results(filtered)
        message = f"Found {limited['total']} routes for path {path_id}."
        if limited["limited"]:
            message += " Large dataset detected; consider applying filters for a more focused list."
        return _success(limited["data"], message)
    except Exception as e:
        return _error("Failed to filter routes", str(e))


def filter_routes_by_status(status: str) -> Dict[str, Any]:
    """Filter routes by status."""
    try:
        repo = RoutesRepository()
        routes = repo.get_all_active()
        filtered = [r for r in routes if (r.get("status") or "").lower() == status.lower()]
        limited = _limit_results(filtered)
        message = f"Found {limited['total']} routes with status '{status}'."
        if limited["limited"]:
            message += " Large dataset detected; consider applying filters for a more focused list."
        return _success(limited["data"], message)
    except Exception as e:
        return _error("Failed to filter routes", str(e))


def filter_routes_by_direction(direction: str) -> Dict[str, Any]:
    """Filter routes by direction (Forward, Reverse, Circular)."""
    try:
        direction_lower = direction.lower()
        repo = RoutesRepository()
        routes = repo.get_all_active()
        filtered = [r for r in routes if (r.get("direction") or "").lower() == direction_lower]
        limited = _limit_results(filtered)
        message = f"Found {limited['total']} routes in direction '{direction}'."
        if limited["limited"]:
            message += " Large dataset detected; consider applying filters for a more focused list."
        return _success(limited["data"], message)
    except Exception as e:
        return _error("Failed to filter routes", str(e))


# ================================================================
# PATH TOOLS
# ================================================================

def get_all_paths() -> Dict[str, Any]:
    """List all active paths."""
    try:
        repo = PathsRepository()
        paths = repo.get_all_active()
        limited = _limit_results(paths)
        message = f"Found {limited['total']} active paths."
        if limited["limited"]:
            message += " Large dataset detected; consider applying filters for a more focused list."
        return _success(limited["data"], message)
    except Exception as e:
        return _error("Failed to fetch paths", str(e))


def get_path_by_id(path_id: int) -> Dict[str, Any]:
    """Get path details by ID."""
    try:
        repo = PathsRepository()
        path = repo.get_by_id(path_id)
        if not path:
            return _error(f"Path {path_id} not found", "Path not found")
        return _success(path, f"Path {path_id} found")
    except Exception as e:
        return _error("Failed to fetch path", str(e))


def create_path_record(path_data: Dict[str, Any], created_by: int = 1) -> Dict[str, Any]:
    """Create a new path."""
    try:
        required_fields = ["path_name", "ordered_list_of_stop_ids"]
        for field in required_fields:
            if not path_data.get(field):
                return _error(f"Field '{field}' is required", "Validation error")
        stop_ids = path_data["ordered_list_of_stop_ids"]
        if not isinstance(stop_ids, list) or len(stop_ids) < 2:
            return _error("Path must have at least two stops", "Validation error")
        return create_path(
            name=str(path_data["path_name"]),
            stop_ids=[int(s) for s in stop_ids],
            description=path_data.get("description"),
            total_distance_km=path_data.get("total_distance_km"),
            estimated_duration_minutes=path_data.get("estimated_duration_minutes"),
            created_by=created_by,
        )
    except ValueError as ve:
        return _error("Invalid stop IDs provided", str(ve))
    except Exception as e:
        return _error("Failed to create path", str(e))


def update_path(path_id: int, update_data: Dict[str, Any], updated_by: int = 1) -> Dict[str, Any]:
    """Update path details."""
    try:
        if not update_data:
            return _error("No update fields provided", "Validation error")
        repo = PathsRepository()
        existing = repo.get_by_id(path_id)
        if not existing:
            return _error(f"Path {path_id} not found", "Path not found")
        data = update_data.copy()
        if "ordered_list_of_stop_ids" in data and data["ordered_list_of_stop_ids"]:
            stop_ids = data["ordered_list_of_stop_ids"]
            if not isinstance(stop_ids, list) or len(stop_ids) < 2:
                return _error("Ordered stops must have at least two entries", "Validation error")
            stops_repo = StopsRepository()
            for stop_id in stop_ids:
                if not stops_repo.get_by_id(int(stop_id)):
                    return _error(f"Stop ID {stop_id} not found", "Validation error")
            data["ordered_list_of_stop_ids"] = [int(s) for s in stop_ids]
        data["updated_by"] = updated_by
        updated = repo.update(path_id, data)
        return _success(updated or {**existing, **data}, f"Path {path_id} updated successfully")
    except ValueError as ve:
        return _error("Invalid stop IDs provided", str(ve))
    except Exception as e:
        return _error("Failed to update path", str(e))


def delete_path(path_id: int, deleted_by: int = 1) -> Dict[str, Any]:
    """Soft delete a path."""
    try:
        repo = PathsRepository()
        existing = repo.get_by_id(path_id)
        if not existing:
            return _error(f"Path {path_id} not found", "Path not found")
        deleted = repo.soft_delete(path_id, deleted_by)
        return _success(deleted or {"path_id": path_id}, f"Path {path_id} deleted successfully")
    except Exception as e:
        return _error("Failed to delete path", str(e))


def filter_paths_by_stop(stop_id: int) -> Dict[str, Any]:
    """Find paths that include a specific stop."""
    try:
        repo = PathsRepository()
        paths = repo.get_all_active()
        filtered = [p for p in paths if int(stop_id) in (p.get("ordered_list_of_stop_ids") or [])]
        limited = _limit_results(filtered)
        message = f"Found {limited['total']} paths containing stop {stop_id}."
        if limited["limited"]:
            message += " Large dataset detected; consider applying filters for a more focused list."
        return _success(limited["data"], message)
    except Exception as e:
        return _error("Failed to filter paths", str(e))





def get_available_drivers() -> Dict[str, Any]:
    """
    Get all drivers that are not currently assigned to any active deployment.
    
    Returns:
        Dict with success status, data (list of drivers), message, and optional error.
    """
    try:
        client = get_client()
        drivers_repo = DriversRepository()
        deployments_repo = DeploymentsRepository()
        
        # Get all active drivers
        all_drivers = drivers_repo.get_all_active()
        
        # Get all active deployments to find assigned driver IDs
        all_deployments = deployments_repo.get_all_active()
        assigned_driver_ids = {dep.get("driver_id") for dep in all_deployments if dep.get("driver_id")}
        
        # Filter out assigned drivers
        available_drivers = [
            driver for driver in all_drivers 
            if driver.get("driver_id") not in assigned_driver_ids
        ]
        
        return {
            "success": True,
            "data": available_drivers,
            "message": f"Found {len(available_drivers)} available drivers"
        }
    except Exception as e:
        return {
            "success": False,
            "data": [],
            "message": "Failed to get available drivers",
            "error": str(e)
        }


# ================================================================
# TRIP TOOLS
# ================================================================

def get_all_trips() -> Dict[str, Any]:
    """Get all active trips."""
    try:
        repo = TripsRepository()
        trips = repo.get_all_active()
        limited = _limit_results(trips)
        message = f"Found {limited['total']} active trips."
        if limited["limited"]:
            message += " Large dataset detected; consider applying filters for a more focused list."
        return _success(limited["data"], message)
    except Exception as e:
        return _error("Failed to fetch trips", str(e))


def get_trip_by_id(trip_id: int) -> Dict[str, Any]:
    """Get trip details by trip_id."""
    try:
        repo = TripsRepository()
        trip = repo.get_by_id(trip_id)
        if not trip:
            return _error(f"Trip {trip_id} not found", "Trip not found")
        return _success(trip, f"Trip {trip_id} found")
    except Exception as e:
        return _error("Failed to fetch trip", str(e))


def create_trip(trip_data: Dict[str, Any], created_by: int = 1) -> Dict[str, Any]:
    """Create a new trip."""
    try:
        required_fields = ["route_id", "display_name"]
        for field in required_fields:
            if not trip_data.get(field):
                return _error(f"Field '{field}' is required", "Validation error")
        payload = trip_data.copy()
        payload["route_id"] = int(payload["route_id"])
        payload["created_by"] = created_by
        repo = TripsRepository()
        trip = repo.create(payload)
        return _success(trip, f"Trip '{trip.get('display_name')}' created successfully")
    except ValueError as ve:
        return _error("Invalid numeric value provided", str(ve))
    except Exception as e:
        return _error("Failed to create trip", str(e))


def update_trip(trip_id: int, update_data: Dict[str, Any], updated_by: int = 1) -> Dict[str, Any]:
    """Update trip details."""
    try:
        if not update_data:
            return _error("No update fields provided", "Validation error")
        repo = TripsRepository()
        existing = repo.get_by_id(trip_id)
        if not existing:
            return _error(f"Trip {trip_id} not found", "Trip not found")
        payload = update_data.copy()
        if "route_id" in payload and payload["route_id"] not in (None, ""):
            payload["route_id"] = int(payload["route_id"])
        if "booking_status_percentage" in payload and payload["booking_status_percentage"] not in (None, ""):
            payload["booking_status_percentage"] = float(payload["booking_status_percentage"])
        if "total_bookings" in payload and payload["total_bookings"] not in (None, ""):
            payload["total_bookings"] = int(payload["total_bookings"])
        payload["updated_by"] = updated_by
        updated = repo.update(trip_id, payload)
        return _success(updated or {**existing, **payload}, f"Trip {trip_id} updated successfully")
    except ValueError as ve:
        return _error("Invalid numeric value provided", str(ve))
    except Exception as e:
        return _error("Failed to update trip", str(e))


def delete_trip(trip_id: int, deleted_by: int = 1) -> Dict[str, Any]:
    """Soft delete a trip."""
    try:
        repo = TripsRepository()
        existing = repo.get_by_id(trip_id)
        if not existing:
            return _error(f"Trip {trip_id} not found", "Trip not found")
        deleted = repo.soft_delete(trip_id, deleted_by)
        return _success(deleted or {"trip_id": trip_id}, f"Trip {trip_id} deleted successfully")
    except Exception as e:
        return _error("Failed to delete trip", str(e))


def filter_trips_by_route(route_id: int) -> Dict[str, Any]:
    """Filter trips by route_id."""
    try:
        repo = TripsRepository()
        trips = repo.get_all_active()
        filtered = [t for t in trips if t.get("route_id") == route_id]
        limited = _limit_results(filtered)
        message = f"Found {limited['total']} trips for route {route_id}."
        if limited["limited"]:
            message += " Large dataset detected; consider applying filters for a more focused list."
        return _success(limited["data"], message)
    except Exception as e:
        return _error("Failed to filter trips", str(e))


def filter_trips_by_status(status: str) -> Dict[str, Any]:
    """Filter trips by status (scheduled, in_progress, completed, etc.)."""
    try:
        repo = TripsRepository()
        trips = repo.get_all_active()
        filtered = [t for t in trips if (t.get("status") or "").lower() == status.lower()]
        limited = _limit_results(filtered)
        message = f"Found {limited['total']} trips with status '{status}'."
        if limited["limited"]:
            message += " Large dataset detected; consider applying filters for a more focused list."
        return _success(limited["data"], message)
    except Exception as e:
        return _error("Failed to filter trips", str(e))


def update_trip_status(trip_id: int, status: str, updated_by: int = 1) -> Dict[str, Any]:
    """Update only the trip status."""
    try:
        repo = TripsRepository()
        existing = repo.get_by_id(trip_id)
        if not existing:
            return _error(f"Trip {trip_id} not found", "Trip not found")
        payload = {"status": status, "updated_by": updated_by}
        updated = repo.update(trip_id, payload)
        return _success(updated or {**existing, **payload}, f"Trip {trip_id} status updated to '{status}'")
    except Exception as e:
        return _error("Failed to update trip status", str(e))


def filter_trips_by_date(trip_date: str) -> Dict[str, Any]:
    """Filter trips by trip_date (ISO format)."""
    try:
        repo = TripsRepository()
        trips = repo.get_all_active()
        filtered = [t for t in trips if (t.get("trip_date") or "").startswith(trip_date)]
        limited = _limit_results(filtered)
        message = f"Found {limited['total']} trips on date '{trip_date}'."
        if limited["limited"]:
            message += " Large dataset detected; consider applying filters for a more focused list."
        return _success(limited["data"], message)
    except Exception as e:
        return _error("Failed to filter trips", str(e))




def get_trip_status(trip_identifier: str) -> Dict[str, Any]:
    """
    Get trip by display_name or trip_id, including booking_status_percentage.
    
    Args:
        trip_identifier: Trip display_name (string) or trip_id (numeric string)
    
    Returns:
        Dict with success status, data (trip info with booking_status_percentage), message, and optional error.
    """
    try:
        trips_repo = TripsRepository()
        
        # Try to parse as integer (trip_id)
        try:
            trip_id = int(trip_identifier)
            trip = trips_repo.get_by_id(trip_id)
        except ValueError:
            # Not a number, treat as display_name
            all_trips = trips_repo.get_all_active()
            trip = None
            for t in all_trips:
                if t.get("display_name") == trip_identifier:
                    trip = t
                    break
        
        if not trip:
            return {
                "success": False,
                "data": None,
                "message": f"Trip '{trip_identifier}' not found",
                "error": "Trip not found"
            }
        
        # Include booking_status_percentage in response
        trip_data = {
            "trip_id": trip.get("trip_id"),
            "display_name": trip.get("display_name"),
            "route_id": trip.get("route_id"),
            "trip_date": trip.get("trip_date"),
            "booking_status_percentage": trip.get("booking_status_percentage", 0.0),
            "total_bookings": trip.get("total_bookings", 0),
            "status": trip.get("status"),
            "live_status": trip.get("live_status")
        }
        
        return {
            "success": True,
            "data": trip_data,
            "message": f"Trip '{trip.get('display_name')}' found with {trip.get('booking_status_percentage', 0)}% bookings"
        }
    except Exception as e:
        return {
            "success": False,
            "data": None,
            "message": "Failed to get trip status",
            "error": str(e)
        }


def list_stops_for_path(path_identifier: str) -> Dict[str, Any]:
    """
    Get path by name or ID, then get all stops from ordered_list_of_stop_ids.
    
    Args:
        path_identifier: Path name (string) or path_id (numeric string)
    
    Returns:
        Dict with success status, data (list of stops in order), message, and optional error.
    """
    try:
        paths_repo = PathsRepository()
        stops_repo = StopsRepository()
        
        # Try to parse as integer (path_id)
        try:
            path_id = int(path_identifier)
            path = paths_repo.get_by_id(path_id)
        except ValueError:
            # Not a number, treat as path_name
            all_paths = paths_repo.get_all_active()
            path = None
            for p in all_paths:
                if p.get("path_name") == path_identifier:
                    path = p
                    break
        
        if not path:
            return {
                "success": False,
                "data": [],
                "message": f"Path '{path_identifier}' not found",
                "error": "Path not found"
            }
        
        # Get ordered list of stop IDs
        stop_ids = path.get("ordered_list_of_stop_ids", [])
        if not stop_ids:
            return {
                "success": True,
                "data": [],
                "message": f"Path '{path.get('path_name')}' has no stops"
            }
        
        # Get all stops in order
        ordered_stops = []
        for stop_id in stop_ids:
            stop = stops_repo.get_by_id(stop_id)
            if stop:
                ordered_stops.append(stop)
        
        return {
            "success": True,
            "data": ordered_stops,
            "message": f"Found {len(ordered_stops)} stops for path '{path.get('path_name')}'"
        }
    except Exception as e:
        return {
            "success": False,
            "data": [],
            "message": "Failed to list stops for path",
            "error": str(e)
        }


def get_routes_by_path(path_identifier: str) -> Dict[str, Any]:
    """
    Get all routes where path_id matches the given path identifier.
    
    Args:
        path_identifier: Path name (string) or path_id (numeric string)
    
    Returns:
        Dict with success status, data (list of routes), message, and optional error.
    """
    try:
        paths_repo = PathsRepository()
        routes_repo = RoutesRepository()
        
        # Try to parse as integer (path_id)
        try:
            path_id = int(path_identifier)
            path = paths_repo.get_by_id(path_id)
            if not path:
                return {
                    "success": False,
                    "data": [],
                    "message": f"Path ID '{path_identifier}' not found",
                    "error": "Path not found"
                }
            actual_path_id = path_id
        except ValueError:
            # Not a number, treat as path_name
            all_paths = paths_repo.get_all_active()
            path = None
            for p in all_paths:
                if p.get("path_name") == path_identifier:
                    path = p
                    break
            
            if not path:
                return {
                    "success": False,
                    "data": [],
                    "message": f"Path '{path_identifier}' not found",
                    "error": "Path not found"
                }
            actual_path_id = path.get("path_id")
        
        # Get all routes for this path
        all_routes = routes_repo.get_all_active()
        routes_for_path = [route for route in all_routes if route.get("path_id") == actual_path_id]
        
        return {
            "success": True,
            "data": routes_for_path,
            "message": f"Found {len(routes_for_path)} routes for path '{path.get('path_name')}'"
        }
    except Exception as e:
        return {
            "success": False,
            "data": [],
            "message": "Failed to get routes by path",
            "error": str(e)
        }


def get_all_active_stops() -> Dict[str, Any]:
    """
    Get all stops where deleted_at IS NULL.
    
    Returns:
        Dict with success status, data (list of stops), message, and optional error.
    """
    try:
        stops_repo = StopsRepository()
        stops = stops_repo.get_all_active()
        
        return {
            "success": True,
            "data": stops,
            "message": f"Found {len(stops)} active stops"
        }
    except Exception as e:
        return {
            "success": False,
            "data": [],
            "message": "Failed to get active stops",
            "error": str(e)
        }


def get_all_active_trips() -> Dict[str, Any]:
    """
    Get all daily_trips where deleted_at IS NULL.
    
    Returns:
        Dict with success status, data (list of trips), message, and optional error.
    """
    try:
        trips_repo = TripsRepository()
        trips = trips_repo.get_all_active()
        
        return {
            "success": True,
            "data": trips,
            "message": f"Found {len(trips)} active trips"
        }
    except Exception as e:
        return {
            "success": False,
            "data": [],
            "message": "Failed to get active trips",
            "error": str(e)
        }


def get_completed_trips_count() -> Dict[str, Any]:
    """
    Get the count of trips where status == 'completed'.

    Returns:
        Dict with success status, data (count), message, and optional error.
    """
    try:
        trips_repo = TripsRepository()
        trips = trips_repo.get_all_active()
        completed_count = sum(1 for trip in trips if (trip.get("status") or "").lower() == "completed")

        return {
            "success": True,
            "data": {"completed_count": completed_count},
            "message": f"Found {completed_count} completed trips"
        }
    except Exception as e:
        return {
            "success": False,
            "data": None,
            "message": "Failed to get completed trips count",
            "error": str(e)
        }


def assign_vehicle_to_trip(vehicle_id: str, driver_id: str, trip_id: str, created_by: int = 1) -> Dict[str, Any]:
    """
    Create a deployment record to assign a vehicle and driver to a trip.
    
    Args:
        vehicle_id: Vehicle ID (as string, will be converted to int)
        driver_id: Driver ID (as string, will be converted to int)
        trip_id: Trip ID (as string, will be converted to int)
        created_by: User ID creating the deployment (default: 1)
    
    Returns:
        Dict with success status, data (deployment record), message, and optional error.
    """
    try:
        deployments_repo = DeploymentsRepository()
        vehicles_repo = VehiclesRepository()
        drivers_repo = DriversRepository()
        trips_repo = TripsRepository()
        
        # Convert string IDs to integers
        vehicle_id_int = int(vehicle_id)
        driver_id_int = int(driver_id)
        trip_id_int = int(trip_id)
        
        # Validate that vehicle, driver, and trip exist
        vehicle = vehicles_repo.get_by_id(vehicle_id_int)
        if not vehicle:
            return {
                "success": False,
                "data": None,
                "message": f"Vehicle ID {vehicle_id} not found",
                "error": "Vehicle not found"
            }
        
        driver = drivers_repo.get_by_id(driver_id_int)
        if not driver:
            return {
                "success": False,
                "data": None,
                "message": f"Driver ID {driver_id} not found",
                "error": "Driver not found"
            }
        
        trip = trips_repo.get_by_id(trip_id_int)
        if not trip:
            return {
                "success": False,
                "data": None,
                "message": f"Trip ID {trip_id} not found",
                "error": "Trip not found"
            }
        
        # Check if deployment already exists for this trip
        all_deployments = deployments_repo.get_all_active()
        existing_deployment = next(
            (dep for dep in all_deployments if dep.get("trip_id") == trip_id_int),
            None
        )
        
        if existing_deployment:
            return {
                "success": False,
                "data": None,
                "message": f"Trip {trip_id} already has a deployment (ID: {existing_deployment.get('deployment_id')})",
                "error": "Deployment already exists"
            }
        
        # Create deployment
        deployment_data = {
            "trip_id": trip_id_int,
            "vehicle_id": vehicle_id_int,
            "driver_id": driver_id_int,
            "deployment_status": "assigned",
            "created_by": created_by
        }
        
        deployment = deployments_repo.create(deployment_data)
        
        return {
            "success": True,
            "data": deployment,
            "message": f"Successfully assigned vehicle {vehicle.get('license_plate')} and driver {driver.get('name')} to trip {trip.get('display_name')}"
        }
    except ValueError as e:
        return {
            "success": False,
            "data": None,
            "message": "Invalid ID format. IDs must be numeric.",
            "error": str(e)
        }
    except Exception as e:
        return {
            "success": False,
            "data": None,
            "message": "Failed to assign vehicle to trip",
            "error": str(e)
        }


def remove_vehicle_from_trip(trip_id: str, deleted_by: int = 1) -> Dict[str, Any]:
    """
    Soft delete deployment where trip_id matches.
    
    Args:
        trip_id: Trip ID (as string, will be converted to int)
        deleted_by: User ID deleting the deployment (default: 1)
    
    Returns:
        Dict with success status, data (deleted deployment), message, and optional error.
    """
    try:
        deployments_repo = DeploymentsRepository()
        trips_repo = TripsRepository()
        
        trip_id_int = int(trip_id)
        
        # Validate trip exists
        trip = trips_repo.get_by_id(trip_id_int)
        if not trip:
            return {
                "success": False,
                "data": None,
                "message": f"Trip ID {trip_id} not found",
                "error": "Trip not found"
            }
        
        # Find deployment for this trip
        all_deployments = deployments_repo.get_all_active()
        deployment = next(
            (dep for dep in all_deployments if dep.get("trip_id") == trip_id_int),
            None
        )
        
        if not deployment:
            return {
                "success": False,
                "data": None,
                "message": f"No deployment found for trip {trip_id}",
                "error": "Deployment not found"
            }
        
        # Soft delete the deployment
        deleted_deployment = deployments_repo.soft_delete(deployment.get("deployment_id"), deleted_by)
        
        return {
            "success": True,
            "data": deleted_deployment,
            "message": f"Successfully removed vehicle assignment from trip {trip.get('display_name')}"
        }
    except ValueError as e:
        return {
            "success": False,
            "data": None,
            "message": "Invalid trip ID format. ID must be numeric.",
            "error": str(e)
        }
    except Exception as e:
        return {
            "success": False,
            "data": None,
            "message": "Failed to remove vehicle from trip",
            "error": str(e)
        }


def create_stop(name: str, latitude: float, longitude: float, description: Optional[str] = None, 
                address: Optional[str] = None, created_by: int = 1) -> Dict[str, Any]:
    """
    Create a new stop with name, coordinates, and optional description/address.
    
    Args:
        name: Stop name
        latitude: Latitude coordinate (-90 to 90)
        longitude: Longitude coordinate (-180 to 180)
        description: Optional stop description
        address: Optional stop address
        created_by: User ID creating the stop (default: 1)
    
    Returns:
        Dict with success status, data (created stop), message, and optional error.
    """
    try:
        stops_repo = StopsRepository()
        
        # Validate coordinates
        if not (-90 <= latitude <= 90):
            return {
                "success": False,
                "data": None,
                "message": "Latitude must be between -90 and 90",
                "error": "Invalid latitude"
            }
        
        if not (-180 <= longitude <= 180):
            return {
                "success": False,
                "data": None,
                "message": "Longitude must be between -180 and 180",
                "error": "Invalid longitude"
            }
        
        # Create stop
        stop_data = {
            "name": name,
            "latitude": latitude,
            "longitude": longitude,
            "description": description,
            "address": address,
            "is_active": True,
            "created_by": created_by
        }
        
        stop = stops_repo.create(stop_data)
        
        return {
            "success": True,
            "data": stop,
            "message": f"Successfully created stop '{name}'"
        }
    except Exception as e:
        return {
            "success": False,
            "data": None,
            "message": "Failed to create stop",
            "error": str(e)
        }


def create_path(name: str, stop_ids: List[int], description: Optional[str] = None,
                total_distance_km: Optional[float] = None, 
                estimated_duration_minutes: Optional[int] = None,
                created_by: int = 1) -> Dict[str, Any]:
    """
    Create a new path with ordered_list_of_stop_ids.
    
    Args:
        name: Path name
        stop_ids: List of stop IDs in order
        description: Optional path description
        total_distance_km: Optional total distance in kilometers
        estimated_duration_minutes: Optional estimated duration in minutes
        created_by: User ID creating the path (default: 1)
    
    Returns:
        Dict with success status, data (created path), message, and optional error.
    """
    try:
        paths_repo = PathsRepository()
        stops_repo = StopsRepository()
        
        if not stop_ids:
            return {
                "success": False,
                "data": None,
                "message": "Path must have at least one stop",
                "error": "Empty stop_ids list"
            }
        
        # Validate that all stop IDs exist
        for stop_id in stop_ids:
            stop = stops_repo.get_by_id(stop_id)
            if not stop:
                return {
                    "success": False,
                    "data": None,
                    "message": f"Stop ID {stop_id} not found",
                    "error": f"Invalid stop_id: {stop_id}"
                }
        
        # Create path
        path_data = {
            "path_name": name,
            "ordered_list_of_stop_ids": stop_ids,
            "description": description,
            "total_distance_km": total_distance_km,
            "estimated_duration_minutes": estimated_duration_minutes,
            "is_active": True,
            "created_by": created_by
        }
        
        path = paths_repo.create(path_data)
        
        return {
            "success": True,
            "data": path,
            "message": f"Successfully created path '{name}' with {len(stop_ids)} stops"
        }
    except Exception as e:
        return {
            "success": False,
            "data": None,
            "message": "Failed to create path",
            "error": str(e)
        }


def create_route(path_id: str, shift_time: str, direction: str, route_display_name: str,
                 start_point: Optional[str] = None, end_point: Optional[str] = None,
                 status: str = "active", notes: Optional[str] = None, created_by: int = 1) -> Dict[str, Any]:
    """
    Create a new route with path_id, shift_time, direction, and route_display_name.
    
    Args:
        path_id: Path ID (as string, will be converted to int)
        shift_time: Time in HH:MM:SS or HH:MM format
        direction: Route direction (Forward, Reverse, or Circular)
        route_display_name: Display name for the route
        start_point: Optional start point name
        end_point: Optional end point name
        status: Route status (default: "active")
        notes: Optional notes
        created_by: User ID creating the route (default: 1)
    
    Returns:
        Dict with success status, data (created route), message, and optional error.
    """
    try:
        routes_repo = RoutesRepository()
        paths_repo = PathsRepository()
        
        path_id_int = int(path_id)
        
        # Validate path exists
        path = paths_repo.get_by_id(path_id_int)
        if not path:
            return {
                "success": False,
                "data": None,
                "message": f"Path ID {path_id} not found",
                "error": "Path not found"
            }
        
        # Validate direction
        valid_directions = ["Forward", "Reverse", "Circular"]
        if direction not in valid_directions:
            return {
                "success": False,
                "data": None,
                "message": f"Direction must be one of: {', '.join(valid_directions)}",
                "error": "Invalid direction"
            }
        
        # Validate status
        valid_statuses = ["active", "deactivated"]
        if status not in valid_statuses:
            return {
                "success": False,
                "data": None,
                "message": f"Status must be one of: {', '.join(valid_statuses)}",
                "error": "Invalid status"
            }
        
        # Parse shift_time - ensure it's in HH:MM:SS format
        time_parts = shift_time.split(":")
        if len(time_parts) == 2:
            shift_time = f"{shift_time}:00"  # Add seconds if missing
        
        # Get start and end points from path if not provided
        if not start_point or not end_point:
            stops_repo = StopsRepository()
            stop_ids = path.get("ordered_list_of_stop_ids", [])
            if stop_ids:
                first_stop = stops_repo.get_by_id(stop_ids[0])
                last_stop = stops_repo.get_by_id(stop_ids[-1])
                if not start_point:
                    start_point = first_stop.get("name") if first_stop else "Unknown"
                if not end_point:
                    end_point = last_stop.get("name") if last_stop else "Unknown"
            else:
                if not start_point:
                    start_point = "Unknown"
                if not end_point:
                    end_point = "Unknown"
        
        # Create route
        route_data = {
            "path_id": path_id_int,
            "route_display_name": route_display_name,
            "shift_time": shift_time,
            "direction": direction,
            "start_point": start_point,
            "end_point": end_point,
            "status": status,
            "notes": notes,
            "created_by": created_by
        }
        
        route = routes_repo.create(route_data)
        
        return {
            "success": True,
            "data": route,
            "message": f"Successfully created route '{route_display_name}'"
        }
    except ValueError as e:
        return {
            "success": False,
            "data": None,
            "message": "Invalid path ID format. ID must be numeric.",
            "error": str(e)
        }
    except Exception as e:
        return {
            "success": False,
            "data": None,
            "message": "Failed to create route",
            "error": str(e)
        }

