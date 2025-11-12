# Backend Architecture Explanation

## Three-Layer Architecture

The backend follows a clean **3-layer architecture**:

```
Frontend Request
      ↓
┌─────────────────┐
│   ROUTES        │  ← HTTP endpoints (API routes)
└─────────────────┘
      ↓
┌─────────────────┐
│   SERVICES      │  ← Business logic
└─────────────────┘
      ↓
┌─────────────────┐
│   REPOSITORIES  │  ← Database access
└─────────────────┘
      ↓
   Database
```

## 1. MODELS (Schemas) - Data Structure

**Location**: `backend/models/schemas.py`

**Purpose**: Define the structure of data (request/response formats)

**What it does**:
- Validates incoming data from frontend
- Defines what data looks like when sending responses
- Type safety (ensures correct data types)

**Example**:
```python
class StopCreate(BaseModel):
    name: str                    # Required field
    latitude: float              # Required field
    longitude: float             # Required field
    description: Optional[str]    # Optional field
```

**Why needed**: 
- Frontend sends JSON → Models validate it's correct
- Backend sends JSON → Models ensure format is consistent

---

## 2. ROUTES - HTTP Endpoints

**Location**: `backend/routes/*.py`

**Purpose**: Define API endpoints (URLs that frontend calls)

**What it does**:
- Receives HTTP requests (GET, POST, PUT, DELETE)
- Calls the service layer
- Returns HTTP responses

**Example**:
```python
@router.get("/api/stops")           # URL: http://localhost:5005/api/stops
async def get_all_stops():
    return service.get_all()        # Calls service
```

**Flow**:
1. Frontend makes request: `GET /api/stops`
2. Route receives it
3. Route calls service
4. Route returns response to frontend

**Why needed**: 
- Frontend needs URLs to call
- Routes handle HTTP protocol (status codes, errors, etc.)

---

## 3. SERVICES - Business Logic

**Location**: `backend/services/*.py`

**Purpose**: Contains business logic and rules

**What it does**:
- Processes data
- Applies business rules
- Calls repositories to access database
- Handles complex operations

**Example**:
```python
def get_all(self):
    """Get all active stops"""
    return self.repository.get_all_active()  # Calls repository
```

**Why needed**:
- Separates business logic from HTTP handling
- Can be reused by different routes
- Easy to test and maintain

---

## Complete Flow Example

**Frontend wants to get all stops:**

```
1. Frontend: GET http://localhost:5005/api/stops
                    ↓
2. ROUTE (stops.py): Receives request
                    ↓
3. SERVICE (stops_service.py): Processes request
                    ↓
4. REPOSITORY (repositories.py): Queries database
                    ↓
5. Database: Returns data
                    ↓
6. REPOSITORY: Returns to service
                    ↓
7. SERVICE: Returns to route
                    ↓
8. ROUTE: Returns JSON to frontend
```

---

## Why This Structure?

✅ **Separation of Concerns**: Each layer has one job
✅ **Easy to Maintain**: Change one layer without affecting others
✅ **Testable**: Can test each layer independently
✅ **Scalable**: Easy to add new features
✅ **Clean Code**: Organized and professional

---

## File Structure

```
backend/
├── models/
│   └── schemas.py          # Data structures (what data looks like)
│
├── routes/
│   ├── stops.py            # HTTP endpoints for stops
│   ├── paths.py             # HTTP endpoints for paths
│   ├── routes.py            # HTTP endpoints for routes
│   ├── vehicles.py          # HTTP endpoints for vehicles
│   ├── drivers.py           # HTTP endpoints for drivers
│   ├── trips.py            # HTTP endpoints for trips
│   └── deployments.py      # HTTP endpoints for deployments
│
└── services/
    ├── stops_service.py     # Business logic for stops
    ├── paths_service.py     # Business logic for paths
    ├── routes_service.py    # Business logic for routes
    ├── vehicles_service.py  # Business logic for vehicles
    ├── drivers_service.py   # Business logic for drivers
    ├── trips_service.py     # Business logic for trips
    └── deployments_service.py  # Business logic for deployments
```

---

## No AI Code

✅ **Removed**: All AI agent code deleted
✅ **Clean**: Only REST API endpoints
✅ **Simple**: Standard CRUD operations
✅ **Ready**: For frontend integration

