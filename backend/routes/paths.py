"""
API routes for paths
"""

from fastapi import APIRouter, HTTPException
from typing import List
from backend.services.paths_service import PathsService
from backend.models.schemas import PathCreate, PathUpdate, PathResponse

router = APIRouter()
service = PathsService()


@router.get("/", response_model=List[PathResponse])
async def get_all_paths():
    """Get all active paths"""
    return service.get_all()


@router.get("/{path_id}", response_model=PathResponse)
async def get_path(path_id: int):
    """Get path by ID"""
    path = service.get_by_id(path_id)
    if not path:
        raise HTTPException(status_code=404, detail="Path not found")
    return path


@router.get("/{path_id}/stops")
async def get_path_stops(path_id: int):
    """Get all stops for a path"""
    stops = service.get_stops_for_path(path_id)
    return {"path_id": path_id, "stops": stops}


@router.post("/", response_model=PathResponse)
async def create_path(path_data: PathCreate):
    """Create a new path"""
    return service.create(path_data)


@router.put("/{path_id}", response_model=PathResponse)
async def update_path(path_id: int, path_data: PathUpdate, updated_by: int = 1):
    """
    Update a path - automatically persists to database
    The updated_at timestamp is automatically set by database trigger
    """
    path = service.update(path_id, path_data, updated_by=updated_by)
    if not path:
        raise HTTPException(status_code=404, detail="Path not found")
    return path


@router.delete("/{path_id}")
async def delete_path(path_id: int, deleted_by: int):
    """Soft delete a path"""
    result = service.soft_delete(path_id, deleted_by)
    if not result:
        raise HTTPException(status_code=404, detail="Path not found")
    return {"message": "Path deleted successfully"}

