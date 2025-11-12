"""
Utility functions for database operations.

Provides helper functions for common database tasks like soft delete,
restore, and querying active records.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
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


# Repository instances (lazy initialization to avoid import-time client creation)
_stops_repo = None
_paths_repo = None
_routes_repo = None
_vehicles_repo = None
_drivers_repo = None
_trips_repo = None
_deployments_repo = None

def _get_stops_repo():
    global _stops_repo
    if _stops_repo is None:
        _stops_repo = StopsRepository()
    return _stops_repo

def _get_paths_repo():
    global _paths_repo
    if _paths_repo is None:
        _paths_repo = PathsRepository()
    return _paths_repo

def _get_routes_repo():
    global _routes_repo
    if _routes_repo is None:
        _routes_repo = RoutesRepository()
    return _routes_repo

def _get_vehicles_repo():
    global _vehicles_repo
    if _vehicles_repo is None:
        _vehicles_repo = VehiclesRepository()
    return _vehicles_repo

def _get_drivers_repo():
    global _drivers_repo
    if _drivers_repo is None:
        _drivers_repo = DriversRepository()
    return _drivers_repo

def _get_trips_repo():
    global _trips_repo
    if _trips_repo is None:
        _trips_repo = TripsRepository()
    return _trips_repo

def _get_deployments_repo():
    global _deployments_repo
    if _deployments_repo is None:
        _deployments_repo = DeploymentsRepository()
    return _deployments_repo


# Soft Delete Functions
def soft_delete_stop(stop_id: int, deleted_by: int) -> Dict[str, Any]:
    """Soft delete a stop"""
    return _get_stops_repo().soft_delete(stop_id, deleted_by)


def soft_delete_path(path_id: int, deleted_by: int) -> Dict[str, Any]:
    """Soft delete a path"""
    return _get_paths_repo().soft_delete(path_id, deleted_by)


def soft_delete_route(route_id: int, deleted_by: int) -> Dict[str, Any]:
    """Soft delete a route"""
    return _get_routes_repo().soft_delete(route_id, deleted_by)


def soft_delete_vehicle(vehicle_id: int, deleted_by: int) -> Dict[str, Any]:
    """Soft delete a vehicle"""
    return _get_vehicles_repo().soft_delete(vehicle_id, deleted_by)


def soft_delete_driver(driver_id: int, deleted_by: int) -> Dict[str, Any]:
    """Soft delete a driver"""
    return _get_drivers_repo().soft_delete(driver_id, deleted_by)


def soft_delete_trip(trip_id: int, deleted_by: int) -> Dict[str, Any]:
    """Soft delete a daily trip"""
    return _get_trips_repo().soft_delete(trip_id, deleted_by)


def soft_delete_deployment(deployment_id: int, deleted_by: int) -> Dict[str, Any]:
    """Soft delete a deployment"""
    return _get_deployments_repo().soft_delete(deployment_id, deleted_by)


# Restore Functions
def restore_stop(stop_id: int, restored_by: int) -> Dict[str, Any]:
    """Restore a soft-deleted stop"""
    client = get_client()
    result = client.table("stops").update({
        "deleted_at": None,
        "deleted_by": None,
        "updated_by": restored_by
    }).eq("stop_id", stop_id).execute()
    return result.data[0] if result.data else {}


# Get Active Records Functions
def get_active_stops() -> List[Dict[str, Any]]:
    """Get all active (non-deleted) stops"""
    return _get_stops_repo().get_all_active()


def get_active_paths() -> List[Dict[str, Any]]:
    """Get all active (non-deleted) paths"""
    return _get_paths_repo().get_all_active()


def get_active_routes() -> List[Dict[str, Any]]:
    """Get all active (non-deleted) routes"""
    return _get_routes_repo().get_all_active()


def get_active_vehicles() -> List[Dict[str, Any]]:
    """Get all active (non-deleted) vehicles"""
    return _get_vehicles_repo().get_all_active()


def get_active_drivers() -> List[Dict[str, Any]]:
    """Get all active (non-deleted) drivers"""
    return _get_drivers_repo().get_all_active()


def get_active_trips() -> List[Dict[str, Any]]:
    """Get all active (non-deleted) daily trips"""
    return _get_trips_repo().get_all_active()


def get_active_deployments() -> List[Dict[str, Any]]:
    """Get all active (non-deleted) deployments"""
    return _get_deployments_repo().get_all_active()

