"""
API routes for stops
"""

from fastapi import APIRouter, HTTPException
from typing import List
from backend.services.stops_service import StopsService
from backend.models.schemas import StopCreate, StopUpdate, StopResponse

router = APIRouter()
service = StopsService()


@router.get("/", response_model=List[StopResponse])
async def get_all_stops():
    """Get all active stops"""
    return service.get_all()


@router.get("/{stop_id}", response_model=StopResponse)
async def get_stop(stop_id: int):
    """Get stop by ID"""
    stop = service.get_by_id(stop_id)
    if not stop:
        raise HTTPException(status_code=404, detail="Stop not found")
    return stop


@router.post("/", response_model=StopResponse)
async def create_stop(stop_data: StopCreate):
    """Create a new stop"""
    try:
        return service.create(stop_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create stop: {str(e)}")


@router.put("/{stop_id}", response_model=StopResponse)
async def update_stop(stop_id: int, stop_data: StopUpdate, updated_by: int = 1):
    """
    Update a stop - automatically persists to database
    The updated_at timestamp is automatically set by database trigger
    """
    stop = service.update(stop_id, stop_data, updated_by=updated_by)
    if not stop:
        raise HTTPException(status_code=404, detail="Stop not found")
    return stop


@router.delete("/{stop_id}")
async def delete_stop(stop_id: int, deleted_by: int):
    """Soft delete a stop"""
    result = service.soft_delete(stop_id, deleted_by)
    if not result:
        raise HTTPException(status_code=404, detail="Stop not found")
    return {"message": "Stop deleted successfully"}

