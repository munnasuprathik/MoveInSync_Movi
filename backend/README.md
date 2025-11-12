# Movi Backend API

Production-ready FastAPI backend for Movi transport management system.

## Structure

```
backend/
├── __init__.py
├── main.py                 # FastAPI application
├── models/
│   ├── __init__.py
│   └── schemas.py         # Pydantic models for request/response
├── routes/
│   ├── __init__.py
│   ├── stops.py           # Stops endpoints
│   ├── paths.py            # Paths endpoints
│   ├── routes.py           # Routes endpoints
│   ├── vehicles.py         # Vehicles endpoints
│   ├── drivers.py          # Drivers endpoints
│   ├── trips.py            # Trips endpoints
│   └── deployments.py      # Deployments endpoints
└── services/
    ├── __init__.py
    ├── stops_service.py
    ├── paths_service.py
    ├── routes_service.py
    ├── vehicles_service.py
    ├── drivers_service.py
    ├── trips_service.py
    └── deployments_service.py
```

## Architecture

- **FastAPI**: Modern, fast web framework
- **Repository Pattern**: Clean data access layer
- **Service Layer**: Business logic separation
- **Pydantic Models**: Type-safe request/response validation
- **RESTful API**: Standard REST endpoints

## Running the Server

### From Project Root (Recommended)
```bash
python run_server.py
```

### Alternative Methods
```bash
# Using Python module
python -m backend

# Using uvicorn directly
uvicorn backend.main:app --reload --host 0.0.0.0 --port 5005
```

The API will be available at:
- **API**: http://localhost:5005
- **Docs**: http://localhost:5005/docs
- **Health**: http://localhost:5005/health

## API Endpoints

### CRUD Operations
- `GET /api/stops` - Get all stops
- `POST /api/stops` - Create stop
- `GET /api/paths` - Get all paths
- `GET /api/routes` - Get all routes
- `GET /api/vehicles` - Get all vehicles
- `GET /api/drivers` - Get all drivers
- `GET /api/trips` - Get all trips
- `GET /api/deployments` - Get all deployments

### Special Endpoints
- `GET /api/vehicles/unassigned` - Get unassigned vehicles
- `GET /api/trips/by-name/{name}` - Get trip by display name
- `GET /api/paths/{path_id}/stops` - Get stops for a path
- `GET /api/routes/by-path/{path_id}` - Get routes using a path

## Features

✅ Full CRUD operations for all tables
✅ Soft delete support
✅ Type-safe request/response models
✅ Automatic API documentation (Swagger)
✅ CORS enabled for frontend integration
✅ Error handling
✅ Production-ready REST API

