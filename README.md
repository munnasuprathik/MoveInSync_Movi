# Movi - Multimodal Transport Agent

A production-ready transport management system built with Supabase database, FastAPI backend, MCP-powered AI assistant, and comprehensive audit trails.

## Project Structure

```
Movi V1/
├── database/              # Database layer (Supabase)
├── backend/               # FastAPI backend API
├── frontend/              # React frontend
├── data/                  # Assignment PDF
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Quick Start

### Prerequisites
- Python 3.10+ with virtual environment
- Node.js 16+ and npm
- Supabase account and project

### 1. Install Backend Dependencies
```bash
# Activate virtual environment
.venv\Scripts\Activate.ps1  # Windows PowerShell
# or
.venv\Scripts\activate.bat  # Windows CMD

# Install dependencies
pip install -r requirements.txt
```

### 2. Set Up Environment Variables
Create `.env` in the project root with:

```
# CRUD API / repository layer
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key

# MCP-powered AI assistant
SUPABASE_PROJECT_REF=your_supabase_project_ref
SUPABASE_ACCESS_TOKEN=your_supabase_service_role_token
ANTHROPIC_API_KEY=your_anthropic_api_key
```

Notes:
- Get Supabase URL/key/project ref from https://supabase.com/dashboard (Project Settings → API)
- Generate a service role access token from Supabase Dashboard → Settings → API
- Create an Anthropic API key at https://console.anthropic.com/
- Keep these secrets safe and never commit `.env`

After configuring the environment variables:
1. Run `database/schema.sql` in the Supabase SQL Editor
2. (Optional) Seed sample data with `python database/init_database.py`

### 3. Start Backend Server
```bash
# From project root
python run_server.py
```

Backend will be available at:
- **API**: http://localhost:5005
- **Docs**: http://localhost:5005/docs
- **Health**: http://localhost:5005/health

### 4. Start Frontend (in new terminal)
```bash
cd frontend
npm install
npm run dev
```

Frontend will be available at:
- **App**: http://localhost:5000

## Components

### Database Layer (`database/`)
- Supabase integration
- Repository pattern
- Soft delete support
- Audit trails

### Backend API (`backend/`)
- FastAPI REST API (mounted under `/api`)
- Full CRUD operations
- Type-safe models
- Auto-generated docs
- MCP/LangGraph chatbot backend exposed via `/agent`, `/api/chat`, `/api/upload-image`
- Auto-persist to database

### Frontend (`frontend/`)
- React with Vite
- Two main pages: Bus Dashboard & Manage Route
- API integration with Axios
- Modern responsive UI
- Chatbot UI component wired to the MCP backend endpoints

## Documentation

- **Main README**: This file (overview and quick start)
- **Database**: `database/README.md` (database schema and operations)
- **Backend**: `backend/README.md` (API endpoints and architecture)
- **Frontend**: `frontend/README.md` (frontend setup and pages)

### Database Schema

The database follows the operational flow: **Stop → Path → Route → Trip**

#### Users Table (for audit trail):
- **Users**: System users for tracking who created/updated/deleted records (user_id, username, email, full_name, role, is_active)

#### Static Assets (for manageRoute page):
- **Stops**: Locations with coordinates, description, address, and status
  - Core: stop_id, name, latitude, longitude
  - Additional: description, address, is_active
  - Audit: created_at, updated_at, created_by, updated_by
  - Soft Delete: deleted_at, deleted_by

- **Paths**: Ordered sequences of stops with distance and duration info
  - Core: path_id, path_name, ordered_list_of_stop_ids
  - Additional: description, total_distance_km, estimated_duration_minutes, is_active
  - Audit: created_at, updated_at, created_by, updated_by
  - Soft Delete: deleted_at, deleted_by

- **Routes**: Paths with assigned times and operational details
  - Core: route_id, path_id, route_display_name, shift_time, direction, start_point, end_point, status
  - Additional: notes
  - Audit: created_at, updated_at, created_by, updated_by
  - Soft Delete: deleted_at, deleted_by

#### Dynamic Assets & Operations (for busDashboard page):
- **Vehicles**: Transport vehicles with comprehensive details
  - Core: vehicle_id, license_plate, type, capacity
  - Additional: make, model, year, color, registration_date, service_dates, is_available, status, notes
  - Audit: created_at, updated_at, created_by, updated_by
  - Soft Delete: deleted_at, deleted_by

- **Drivers**: Driver information with license and contact details
  - Core: driver_id, name, phone_number
  - Additional: email, license_number, license_expiry_date, address, emergency_contacts, is_available, status, notes
  - Audit: created_at, updated_at, created_by, updated_by
  - Soft Delete: deleted_at, deleted_by

- **DailyTrips**: Daily trip instances with booking and status tracking
  - Core: trip_id, route_id, display_name, booking_status_percentage, live_status
  - Additional: trip_date, scheduled/actual departure/arrival times, total_bookings, status, notes
  - Audit: created_at, updated_at, created_by, updated_by
  - Soft Delete: deleted_at, deleted_by

- **Deployments**: Links vehicles and drivers to trips with status tracking
  - Core: deployment_id, trip_id, vehicle_id, driver_id
  - Additional: deployment_status, assigned_at, confirmed_at, notes
  - Audit: created_at, updated_at, created_by, updated_by
  - Soft Delete: deleted_at, deleted_by

### Key Features

#### 1. Soft Delete Support
- All tables support soft delete via `deleted_at` and `deleted_by` columns
- Records are never physically deleted, allowing for data recovery and audit trails
- Use `database/soft_delete_utils.py` for soft delete operations
- Views are available for easy querying of active (non-deleted) records

#### 2. Complete Audit Trail (Who Columns)
- **created_by**: User who created the record
- **updated_by**: User who last updated the record
- **deleted_by**: User who soft-deleted the record
- **created_at**: Timestamp when record was created
- **updated_at**: Automatically updated on record modification (via triggers)

#### 3. Automatic Timestamps
- Triggers automatically update `updated_at` column on any record modification
- No manual intervention needed

#### 4. Comprehensive Indexes
- Foreign key indexes for join performance
- Soft delete indexes for efficient filtering of active records
- Audit column indexes for tracking user actions
- Additional indexes on frequently queried columns (license_plate, status, dates, etc.)

#### 5. Database Views
- Pre-defined views for active records: `active_stops`, `active_paths`, `active_routes`, `active_vehicles`, `active_drivers`, `active_daily_trips`, `active_deployments`
- Simplifies queries by automatically filtering out soft-deleted records

### Setup Instructions

#### Prerequisites
- Python 3.8 or higher
- A Supabase account and project

#### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

#### Step 2: Configure Supabase

1. Create a new project on [Supabase](https://supabase.com)
2. Copy your project URL and anon key from the project settings
3. Create a `.env` file in the root directory:

```env
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
```

#### Step 3: Create Database Schema

1. Go to your Supabase Dashboard
2. Navigate to **SQL Editor** > **New Query**
3. Open `database/schema.sql` and copy its contents
4. Paste and execute the SQL in the Supabase SQL Editor

#### Step 4: Initialize Database (Optional - for development/testing)

For initial setup with sample data, run from project root:

```bash
# From project root (recommended)
python database/init_database.py

# Or from database directory
cd database
python init_database.py
```

This creates extensive Bengaluru-specific sample data for development and testing purposes.
The script will:
- Ask if you want to clear existing data
- Create admin user
- Populate 45+ stops, 20 paths, 80 routes, 23 vehicles, 30 drivers, 560+ trips

### Database Structure

```
stops
  ↓
paths (references stops via ordered_list_of_stop_ids)
  ↓
routes (references paths)
  ↓
daily_trips (references routes)
  ↓
deployments (links vehicles and drivers to trips)
```

### Verification

After running the initialization script, you can verify the data in your Supabase Dashboard:
- Go to **Table Editor** to view all tables
- Check that data has been populated correctly
- Verify relationships between tables

### Soft Delete Operations

Use the utility functions in `database/soft_delete_utils.py`:

```python
from database.soft_delete_utils import soft_delete_stop, restore_stop, get_active_stops

# Soft delete a stop
soft_delete_stop(stop_id=1, deleted_by=user_id)

# Restore a soft-deleted stop
restore_stop(stop_id=1, restored_by=user_id)

# Get only active (non-deleted) stops
active_stops = get_active_stops()
```

Similar functions are available for all tables: `soft_delete_path`, `soft_delete_route`, `soft_delete_vehicle`, `soft_delete_driver`, `soft_delete_trip`, `soft_delete_deployment`, and their corresponding `get_active_*` functions.

### Querying Active Records

Always filter by `deleted_at IS NULL` when querying active records:

```python
# Using Supabase client
active_routes = supabase.table("routes").select("*").is_("deleted_at", None).execute()

# Or use the views
active_routes = supabase.table("active_routes").select("*").execute()
```

### Notes

- The schema uses PostgreSQL (Supabase's underlying database)
- Foreign key constraints use `ON DELETE RESTRICT` to prevent accidental data loss
- All tables include comprehensive audit columns for tracking who did what and when
- Soft delete is implemented across all tables for data recovery and compliance
- Automatic triggers update `updated_at` timestamps on record modifications
- Indexes are optimized for both active record queries and soft delete filtering
- The dummy data reflects realistic transport operations with full metadata

