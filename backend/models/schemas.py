"""
Pydantic schemas for request/response models
"""

from typing import Optional, List
from datetime import datetime, date, time
from pydantic import BaseModel, Field


# Base schemas
class BaseSchema(BaseModel):
    """Base schema with common fields"""
    class Config:
        from_attributes = True


# Stop schemas
class StopBase(BaseSchema):
    name: str
    latitude: float
    longitude: float
    description: Optional[str] = None
    address: Optional[str] = None
    is_active: bool = True


class StopCreate(StopBase):
    created_by: Optional[int] = None


class StopUpdate(BaseSchema):
    name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    description: Optional[str] = None
    address: Optional[str] = None
    is_active: Optional[bool] = None
    updated_by: Optional[int] = None


class StopResponse(StopBase):
    stop_id: int
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[int] = None


# Path schemas
class PathBase(BaseSchema):
    path_name: str
    ordered_list_of_stop_ids: List[int]
    description: Optional[str] = None
    total_distance_km: Optional[float] = None
    estimated_duration_minutes: Optional[int] = None
    is_active: bool = True


class PathCreate(PathBase):
    created_by: Optional[int] = None


class PathUpdate(BaseSchema):
    path_name: Optional[str] = None
    ordered_list_of_stop_ids: Optional[List[int]] = None
    description: Optional[str] = None
    total_distance_km: Optional[float] = None
    estimated_duration_minutes: Optional[int] = None
    is_active: Optional[bool] = None
    updated_by: Optional[int] = None


class PathResponse(PathBase):
    path_id: int
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[int] = None


# Route schemas
class RouteBase(BaseSchema):
    path_id: int
    route_display_name: str
    shift_time: time
    direction: str = Field(..., pattern="^(Forward|Reverse|Circular)$")
    start_point: str
    end_point: str
    status: str = Field(default="active", pattern="^(active|deactivated)$")
    notes: Optional[str] = None


class RouteCreate(RouteBase):
    created_by: Optional[int] = None


class RouteUpdate(BaseSchema):
    path_id: Optional[int] = None
    route_display_name: Optional[str] = None
    shift_time: Optional[time] = None
    direction: Optional[str] = None
    start_point: Optional[str] = None
    end_point: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    updated_by: Optional[int] = None


class RouteResponse(RouteBase):
    route_id: int
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[int] = None


# Vehicle schemas
class VehicleBase(BaseSchema):
    license_plate: str
    type: str = Field(..., pattern="^(Bus|Cab)$")
    capacity: int = Field(..., gt=0)
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    color: Optional[str] = None
    is_available: bool = True
    status: str = Field(default="active", pattern="^(active|maintenance|retired)$")
    notes: Optional[str] = None


class VehicleCreate(VehicleBase):
    created_by: Optional[int] = None


class VehicleUpdate(BaseSchema):
    license_plate: Optional[str] = None
    type: Optional[str] = None
    capacity: Optional[int] = None
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    color: Optional[str] = None
    is_available: Optional[bool] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    updated_by: Optional[int] = None


class VehicleResponse(VehicleBase):
    vehicle_id: int
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[int] = None


# Driver schemas
class DriverBase(BaseSchema):
    name: str
    phone_number: str
    email: Optional[str] = None
    license_number: Optional[str] = None
    is_available: bool = True
    status: str = Field(default="active", pattern="^(active|on_leave|suspended)$")
    notes: Optional[str] = None


class DriverCreate(DriverBase):
    created_by: Optional[int] = None


class DriverUpdate(BaseSchema):
    name: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    license_number: Optional[str] = None
    is_available: Optional[bool] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    updated_by: Optional[int] = None


class DriverResponse(DriverBase):
    driver_id: int
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[int] = None


# Trip schemas
class TripBase(BaseSchema):
    route_id: int
    display_name: str
    trip_date: date
    booking_status_percentage: float = Field(default=0.0, ge=0, le=100)
    live_status: Optional[str] = None
    total_bookings: int = Field(default=0, ge=0)
    status: str = Field(default="scheduled", pattern="^(scheduled|in_progress|completed|cancelled)$")
    notes: Optional[str] = None


class TripCreate(TripBase):
    created_by: Optional[int] = None


class TripUpdate(BaseSchema):
    route_id: Optional[int] = None
    display_name: Optional[str] = None
    trip_date: Optional[date] = None
    booking_status_percentage: Optional[float] = None
    live_status: Optional[str] = None
    total_bookings: Optional[int] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    updated_by: Optional[int] = None


class TripResponse(TripBase):
    trip_id: int
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[int] = None


# Deployment schemas
class DeploymentBase(BaseSchema):
    trip_id: int
    vehicle_id: int
    driver_id: int
    deployment_status: str = Field(default="assigned", pattern="^(assigned|confirmed|in_transit|completed|cancelled)$")
    notes: Optional[str] = None


class DeploymentCreate(DeploymentBase):
    created_by: Optional[int] = None


class DeploymentUpdate(BaseSchema):
    trip_id: Optional[int] = None
    vehicle_id: Optional[int] = None
    driver_id: Optional[int] = None
    deployment_status: Optional[str] = None
    notes: Optional[str] = None
    updated_by: Optional[int] = None


class DeploymentResponse(DeploymentBase):
    deployment_id: int
    assigned_at: datetime
    confirmed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[int] = None


# Chatbot schemas
class ChatMessage(BaseSchema):
    role: str  # 'user' or 'assistant'
    content: str


class ChatRequest(BaseSchema):
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 500


class ChatResponse(BaseSchema):
    message: str
    role: str = "assistant"

