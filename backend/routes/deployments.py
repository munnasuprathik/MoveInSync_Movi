"""
API routes for deployments
"""

from fastapi import APIRouter, HTTPException
from typing import List
from backend.services.deployments_service import DeploymentsService
from backend.models.schemas import DeploymentCreate, DeploymentUpdate, DeploymentResponse

router = APIRouter()
service = DeploymentsService()


@router.get("/", response_model=List[DeploymentResponse])
async def get_all_deployments():
    """Get all active deployments"""
    return service.get_all()


@router.get("/{deployment_id}", response_model=DeploymentResponse)
async def get_deployment(deployment_id: int):
    """Get deployment by ID"""
    deployment = service.get_by_id(deployment_id)
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    return deployment


@router.get("/by-trip/{trip_id}")
async def get_deployment_by_trip(trip_id: int):
    """Get deployment for a specific trip. Returns null if no deployment exists."""
    deployment = service.get_by_trip_id(trip_id)
    # Return null instead of 404 - "no deployment" is a valid state, not an error
    return deployment if deployment else None


@router.post("/", response_model=DeploymentResponse)
async def create_deployment(deployment_data: DeploymentCreate):
    """Create a new deployment"""
    return service.create(deployment_data)


@router.put("/{deployment_id}", response_model=DeploymentResponse)
async def update_deployment(deployment_id: int, deployment_data: DeploymentUpdate, updated_by: int = 1):
    """
    Update a deployment - automatically persists to database
    The updated_at timestamp is automatically set by database trigger
    """
    deployment = service.update(deployment_id, deployment_data, updated_by=updated_by)
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    return deployment


@router.delete("/{deployment_id}")
async def delete_deployment(deployment_id: int, deleted_by: int):
    """Soft delete a deployment"""
    result = service.soft_delete(deployment_id, deleted_by)
    if not result:
        raise HTTPException(status_code=404, detail="Deployment not found")
    return {"message": "Deployment deleted successfully"}

