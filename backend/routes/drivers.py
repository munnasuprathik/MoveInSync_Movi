"""
API routes for drivers
"""

from fastapi import APIRouter, HTTPException
from typing import List
from backend.services.drivers_service import DriversService
from backend.models.schemas import DriverCreate, DriverUpdate, DriverResponse

router = APIRouter()
service = DriversService()


@router.get("/", response_model=List[DriverResponse])
async def get_all_drivers():
    """Get all active drivers"""
    return service.get_all()


@router.get("/{driver_id}", response_model=DriverResponse)
async def get_driver(driver_id: int):
    """Get driver by ID"""
    driver = service.get_by_id(driver_id)
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    return driver


@router.post("/", response_model=DriverResponse)
async def create_driver(driver_data: DriverCreate):
    """Create a new driver"""
    return service.create(driver_data)


@router.put("/{driver_id}", response_model=DriverResponse)
async def update_driver(driver_id: int, driver_data: DriverUpdate, updated_by: int = 1):
    """
    Update a driver - automatically persists to database
    The updated_at timestamp is automatically set by database trigger
    """
    driver = service.update(driver_id, driver_data, updated_by=updated_by)
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    return driver


@router.delete("/{driver_id}")
async def delete_driver(driver_id: int, deleted_by: int):
    """Soft delete a driver"""
    result = service.soft_delete(driver_id, deleted_by)
    if not result:
        raise HTTPException(status_code=404, detail="Driver not found")
    return {"message": "Driver deleted successfully"}

