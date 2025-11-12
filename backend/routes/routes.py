"""
API routes for routes
"""

from fastapi import APIRouter, HTTPException
from typing import List
from backend.services.routes_service import RoutesService
from backend.models.schemas import RouteCreate, RouteUpdate, RouteResponse

router = APIRouter()
service = RoutesService()


@router.get("/", response_model=List[RouteResponse])
async def get_all_routes():
    """Get all active routes"""
    return service.get_all()


@router.get("/{route_id}", response_model=RouteResponse)
async def get_route(route_id: int):
    """Get route by ID"""
    route = service.get_by_id(route_id)
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    return route


@router.get("/by-path/{path_id}")
async def get_routes_by_path(path_id: int):
    """Get all routes that use a specific path"""
    routes = service.get_routes_by_path(path_id)
    return {"path_id": path_id, "routes": routes}


@router.post("/", response_model=RouteResponse)
async def create_route(route_data: RouteCreate):
    """Create a new route"""
    return service.create(route_data)


@router.put("/{route_id}", response_model=RouteResponse)
async def update_route(route_id: int, route_data: RouteUpdate, updated_by: int = 1):
    """
    Update a route - automatically persists to database
    The updated_at timestamp is automatically set by database trigger
    """
    route = service.update(route_id, route_data, updated_by=updated_by)
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    return route


@router.delete("/{route_id}")
async def delete_route(route_id: int, deleted_by: int):
    """Soft delete a route"""
    result = service.soft_delete(route_id, deleted_by)
    if not result:
        raise HTTPException(status_code=404, detail="Route not found")
    return {"message": "Route deleted successfully"}

