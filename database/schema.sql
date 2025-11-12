-- ============================================================================
-- Movi Database Schema with Soft Delete and Audit Columns (Who Columns)
-- ============================================================================

-- Users Table (for audit trail - created_by, updated_by, deleted_by)
CREATE TABLE IF NOT EXISTS users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'manager',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(user_id),
    updated_by INTEGER REFERENCES users(user_id),
    deleted_at TIMESTAMP,
    deleted_by INTEGER REFERENCES users(user_id)
);

-- ============================================================================
-- Static Assets Schema (for manageRoute page)
-- ============================================================================

-- Stops Table
CREATE TABLE IF NOT EXISTS stops (
    stop_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,
    description TEXT,
    address TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    -- Audit columns (Who columns)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(user_id),
    updated_by INTEGER REFERENCES users(user_id),
    -- Soft delete columns
    deleted_at TIMESTAMP,
    deleted_by INTEGER REFERENCES users(user_id)
);

-- Paths Table
CREATE TABLE IF NOT EXISTS paths (
    path_id SERIAL PRIMARY KEY,
    path_name VARCHAR(255) NOT NULL,
    ordered_list_of_stop_ids INTEGER[] NOT NULL,
    description TEXT,
    total_distance_km DECIMAL(10, 2),
    estimated_duration_minutes INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    -- Audit columns (Who columns)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(user_id),
    updated_by INTEGER REFERENCES users(user_id),
    -- Soft delete columns
    deleted_at TIMESTAMP,
    deleted_by INTEGER REFERENCES users(user_id)
);

-- Routes Table (combines Path + Time)
CREATE TABLE IF NOT EXISTS routes (
    route_id SERIAL PRIMARY KEY,
    path_id INTEGER NOT NULL REFERENCES paths(path_id) ON DELETE RESTRICT,
    route_display_name VARCHAR(255) NOT NULL,
    shift_time TIME NOT NULL,
    direction VARCHAR(50) NOT NULL CHECK (direction IN ('Forward', 'Reverse', 'Circular')),
    start_point VARCHAR(255) NOT NULL,
    end_point VARCHAR(255) NOT NULL,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'deactivated')),
    notes TEXT,
    -- Audit columns (Who columns)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(user_id),
    updated_by INTEGER REFERENCES users(user_id),
    -- Soft delete columns
    deleted_at TIMESTAMP,
    deleted_by INTEGER REFERENCES users(user_id)
);

-- ============================================================================
-- Dynamic Assets & Operations (for busDashboard page)
-- ============================================================================

-- Vehicles Table
CREATE TABLE IF NOT EXISTS vehicles (
    vehicle_id SERIAL PRIMARY KEY,
    license_plate VARCHAR(20) UNIQUE NOT NULL,
    type VARCHAR(20) NOT NULL CHECK (type IN ('Bus', 'Cab')),
    capacity INTEGER NOT NULL CHECK (capacity > 0),
    make VARCHAR(100),
    model VARCHAR(100),
    year INTEGER,
    color VARCHAR(50),
    registration_date DATE,
    last_service_date DATE,
    next_service_date DATE,
    is_available BOOLEAN DEFAULT TRUE,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'maintenance', 'retired')),
    notes TEXT,
    -- Audit columns (Who columns)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(user_id),
    updated_by INTEGER REFERENCES users(user_id),
    -- Soft delete columns
    deleted_at TIMESTAMP,
    deleted_by INTEGER REFERENCES users(user_id)
);

-- Drivers Table
CREATE TABLE IF NOT EXISTS drivers (
    driver_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    phone_number VARCHAR(20) NOT NULL,
    email VARCHAR(255),
    license_number VARCHAR(50) UNIQUE,
    license_expiry_date DATE,
    address TEXT,
    emergency_contact_name VARCHAR(255),
    emergency_contact_phone VARCHAR(20),
    is_available BOOLEAN DEFAULT TRUE,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'on_leave', 'suspended')),
    notes TEXT,
    -- Audit columns (Who columns)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(user_id),
    updated_by INTEGER REFERENCES users(user_id),
    -- Soft delete columns
    deleted_at TIMESTAMP,
    deleted_by INTEGER REFERENCES users(user_id)
);

-- DailyTrips Table
CREATE TABLE IF NOT EXISTS daily_trips (
    trip_id SERIAL PRIMARY KEY,
    route_id INTEGER NOT NULL REFERENCES routes(route_id) ON DELETE RESTRICT,
    display_name VARCHAR(255) NOT NULL,
    trip_date DATE DEFAULT CURRENT_DATE,
    booking_status_percentage DECIMAL(5, 2) DEFAULT 0.00 CHECK (booking_status_percentage >= 0 AND booking_status_percentage <= 100),
    live_status VARCHAR(50),
    scheduled_departure_time TIMESTAMP,
    actual_departure_time TIMESTAMP,
    scheduled_arrival_time TIMESTAMP,
    actual_arrival_time TIMESTAMP,
    total_bookings INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'in_progress', 'completed', 'cancelled')),
    notes TEXT,
    -- Audit columns (Who columns)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(user_id),
    updated_by INTEGER REFERENCES users(user_id),
    -- Soft delete columns
    deleted_at TIMESTAMP,
    deleted_by INTEGER REFERENCES users(user_id)
);

-- Deployments Table (link between vehicles and trips)
CREATE TABLE IF NOT EXISTS deployments (
    deployment_id SERIAL PRIMARY KEY,
    trip_id INTEGER NOT NULL REFERENCES daily_trips(trip_id) ON DELETE RESTRICT,
    vehicle_id INTEGER NOT NULL REFERENCES vehicles(vehicle_id) ON DELETE RESTRICT,
    driver_id INTEGER NOT NULL REFERENCES drivers(driver_id) ON DELETE RESTRICT,
    deployment_status VARCHAR(20) DEFAULT 'assigned' CHECK (deployment_status IN ('assigned', 'confirmed', 'in_transit', 'completed', 'cancelled')),
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    confirmed_at TIMESTAMP,
    notes TEXT,
    -- Audit columns (Who columns)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(user_id),
    updated_by INTEGER REFERENCES users(user_id),
    -- Soft delete columns
    deleted_at TIMESTAMP,
    deleted_by INTEGER REFERENCES users(user_id),
    -- Ensure unique active deployment per trip
    UNIQUE(trip_id, vehicle_id)
);

-- ============================================================================
-- Indexes for Performance
-- ============================================================================

-- Foreign key indexes
CREATE INDEX IF NOT EXISTS idx_routes_path_id ON routes(path_id) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_daily_trips_route_id ON daily_trips(route_id) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_deployments_trip_id ON deployments(trip_id) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_deployments_vehicle_id ON deployments(vehicle_id) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_deployments_driver_id ON deployments(driver_id) WHERE deleted_at IS NULL;

-- Soft delete indexes (for efficient filtering of non-deleted records)
CREATE INDEX IF NOT EXISTS idx_stops_deleted_at ON stops(deleted_at) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_paths_deleted_at ON paths(deleted_at) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_routes_deleted_at ON routes(deleted_at) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_vehicles_deleted_at ON vehicles(deleted_at) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_drivers_deleted_at ON drivers(deleted_at) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_daily_trips_deleted_at ON daily_trips(deleted_at) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_deployments_deleted_at ON deployments(deleted_at) WHERE deleted_at IS NULL;

-- Audit column indexes
CREATE INDEX IF NOT EXISTS idx_stops_created_by ON stops(created_by) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_paths_created_by ON paths(created_by) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_routes_created_by ON routes(created_by) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_vehicles_created_by ON vehicles(created_by) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_drivers_created_by ON drivers(created_by) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_daily_trips_created_by ON daily_trips(created_by) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_deployments_created_by ON deployments(created_by) WHERE deleted_at IS NULL;

-- Additional useful indexes
CREATE INDEX IF NOT EXISTS idx_vehicles_license_plate ON vehicles(license_plate) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_vehicles_type ON vehicles(type) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_drivers_license_number ON drivers(license_number) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_daily_trips_date ON daily_trips(trip_date) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_daily_trips_status ON daily_trips(status) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_routes_status ON routes(status) WHERE deleted_at IS NULL;

-- ============================================================================
-- Functions and Triggers for Automatic updated_at
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for automatic updated_at on all tables
CREATE TRIGGER update_stops_updated_at BEFORE UPDATE ON stops
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_paths_updated_at BEFORE UPDATE ON paths
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_routes_updated_at BEFORE UPDATE ON routes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_vehicles_updated_at BEFORE UPDATE ON vehicles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_drivers_updated_at BEFORE UPDATE ON drivers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_daily_trips_updated_at BEFORE UPDATE ON daily_trips
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_deployments_updated_at BEFORE UPDATE ON deployments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- Views for Non-Deleted Records (Optional - for easier querying)
-- ============================================================================

CREATE OR REPLACE VIEW active_stops AS
SELECT * FROM stops WHERE deleted_at IS NULL;

CREATE OR REPLACE VIEW active_paths AS
SELECT * FROM paths WHERE deleted_at IS NULL;

CREATE OR REPLACE VIEW active_routes AS
SELECT * FROM routes WHERE deleted_at IS NULL;

CREATE OR REPLACE VIEW active_vehicles AS
SELECT * FROM vehicles WHERE deleted_at IS NULL;

CREATE OR REPLACE VIEW active_drivers AS
SELECT * FROM drivers WHERE deleted_at IS NULL;

CREATE OR REPLACE VIEW active_daily_trips AS
SELECT * FROM daily_trips WHERE deleted_at IS NULL;

CREATE OR REPLACE VIEW active_deployments AS
SELECT * FROM deployments WHERE deleted_at IS NULL;