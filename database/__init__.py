"""
Database module for Movi transport management system.

This module provides:
- Database client connection (Supabase)
- Repository pattern for data access
- Utility functions for common operations
"""

from database.client import get_client, reset_client
from database.repositories import (
    StopsRepository,
    PathsRepository,
    RoutesRepository,
    VehiclesRepository,
    DriversRepository,
    TripsRepository,
    DeploymentsRepository
)
from database.utils import (
    get_active_stops,
    get_active_paths,
    get_active_routes,
    get_active_vehicles,
    get_active_drivers,
    get_active_trips,
    get_active_deployments,
    soft_delete_stop,
    soft_delete_path,
    soft_delete_route,
    soft_delete_vehicle,
    soft_delete_driver,
    soft_delete_trip,
    soft_delete_deployment,
    restore_stop
)

__all__ = [
    # Client
    'get_client',
    'reset_client',
    # Repositories
    'StopsRepository',
    'PathsRepository',
    'RoutesRepository',
    'VehiclesRepository',
    'DriversRepository',
    'TripsRepository',
    'DeploymentsRepository',
    # Utilities
    'get_active_stops',
    'get_active_paths',
    'get_active_routes',
    'get_active_vehicles',
    'get_active_drivers',
    'get_active_trips',
    'get_active_deployments',
    'soft_delete_stop',
    'soft_delete_path',
    'soft_delete_route',
    'soft_delete_vehicle',
    'soft_delete_driver',
    'soft_delete_trip',
    'soft_delete_deployment',
    'restore_stop',
]

