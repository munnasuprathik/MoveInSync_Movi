"""
API routes for vehicles
"""

from fastapi import APIRouter, HTTPException
from typing import List
from backend.services.vehicles_service import VehiclesService
from backend.models.schemas import VehicleCreate, VehicleUpdate, VehicleResponse

router = APIRouter()
service = VehiclesService()


@router.get("/", response_model=List[VehicleResponse])
async def get_all_vehicles():
    """Get all active vehicles"""
    return service.get_all()


@router.get("/unassigned")
async def get_unassigned_vehicles():
    """Get vehicles that are not assigned to any trip"""
    return service.get_unassigned_vehicles()


@router.get("/{vehicle_id}", response_model=VehicleResponse)
async def get_vehicle(vehicle_id: int):
    """Get vehicle by ID"""
    vehicle = service.get_by_id(vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return vehicle


@router.post("/", response_model=VehicleResponse)
async def create_vehicle(vehicle_data: VehicleCreate):
    """Create a new vehicle"""
    return service.create(vehicle_data)


@router.put("/{vehicle_id}", response_model=VehicleResponse)
async def update_vehicle(vehicle_id: int, vehicle_data: VehicleUpdate, updated_by: int = 1):
    """
    Update a vehicle - automatically persists to database
    The updated_at timestamp is automatically set by database trigger
    """
    vehicle = service.update(vehicle_id, vehicle_data, updated_by=updated_by)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return vehicle


@router.delete("/{vehicle_id}")
async def delete_vehicle(vehicle_id: int, deleted_by: int):
    """Soft delete a vehicle"""
    result = service.soft_delete(vehicle_id, deleted_by)
    if not result:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return {"message": "Vehicle deleted successfully"}

