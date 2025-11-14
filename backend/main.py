"""
FastAPI application for Movi backend API with LangGraph agent integration
"""

import sys
from pathlib import Path

# Add project root to Python path (allows running from any directory)
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import CRUD routers
from backend.routes import stops, paths, routes, vehicles, drivers, trips, deployments

app = FastAPI(
    title="Movi API",
    description="Backend API for Movi transport management system",
    version="2.0.0"
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5000", "*"],  # Allow frontend origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include CRUD routers
app.include_router(stops.router, prefix="/api/stops", tags=["Stops"])
app.include_router(paths.router, prefix="/api/paths", tags=["Paths"])
app.include_router(routes.router, prefix="/api/routes", tags=["Routes"])
app.include_router(vehicles.router, prefix="/api/vehicles", tags=["Vehicles"])
app.include_router(drivers.router, prefix="/api/drivers", tags=["Drivers"])
app.include_router(trips.router, prefix="/api/trips", tags=["Trips"])
app.include_router(deployments.router, prefix="/api/deployments", tags=["Deployments"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Movi API",
        "version": "2.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

