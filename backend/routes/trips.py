"""
API routes for trips
"""

from fastapi import APIRouter, HTTPException
from typing import List
from backend.services.trips_service import TripsService
from backend.models.schemas import TripCreate, TripUpdate, TripResponse

router = APIRouter()
service = TripsService()


@router.get("/", response_model=List[TripResponse])
async def get_all_trips():
    """Get all active trips"""
    return service.get_all()


@router.get("/{trip_id}", response_model=TripResponse)
async def get_trip(trip_id: int):
    """Get trip by ID"""
    trip = service.get_by_id(trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip


@router.get("/by-name/{display_name}")
async def get_trip_by_name(display_name: str):
    """Get trip by display name"""
    trip = service.get_by_display_name(display_name)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip


@router.post("/", response_model=TripResponse)
async def create_trip(trip_data: TripCreate):
    """Create a new trip"""
    return service.create(trip_data)


@router.put("/{trip_id}", response_model=TripResponse)
async def update_trip(trip_id: int, trip_data: TripUpdate, updated_by: int = 1):
    """
    Update a trip - automatically persists to database
    The updated_at timestamp is automatically set by database trigger
    """
    trip = service.update(trip_id, trip_data, updated_by=updated_by)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip


@router.delete("/{trip_id}")
async def delete_trip(trip_id: int, deleted_by: int):
    """Soft delete a trip"""
    result = service.soft_delete(trip_id, deleted_by)
    if not result:
        raise HTTPException(status_code=404, detail="Trip not found")
    return {"message": "Trip deleted successfully"}

