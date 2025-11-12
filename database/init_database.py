"""
Database initialization script for Movi - Bengaluru Transport System

This script populates the database with extensive Bengaluru-specific data.
All locations, paths, routes, vehicles, and drivers are unique and Bengaluru-based.
Run this after setting up the database schema via schema.sql in Supabase SQL Editor.

Usage:
    From project root: python database/init_database.py
    Or: cd database && python init_database.py
"""

import sys
from pathlib import Path
from datetime import date, timedelta

# Add project root to Python path (allows running from any directory)
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from database.client import get_client


def clear_existing_data():
    """Clear all existing data from tables (soft delete)"""
    print("Clearing existing data...")
    supabase = get_client()
    
    # Map tables to their primary key column names
    table_pk_map = {
        "stops": "stop_id",
        "paths": "path_id",
        "routes": "route_id",
        "vehicles": "vehicle_id",
        "drivers": "driver_id",
        "daily_trips": "trip_id",
        "deployments": "deployment_id"
    }
    
    cleared_count = 0
    for table, pk_column in table_pk_map.items():
        try:
            # Get all active records (not soft deleted)
            result = supabase.table(table).select(pk_column).is_("deleted_at", "null").execute()
            if result.data:
                # Soft delete all active records
                for record in result.data:
                    record_id = record.get(pk_column)
                    if record_id:
                        try:
                            from datetime import datetime
                            supabase.table(table).update({
                                "deleted_at": datetime.now().isoformat(),
                                "deleted_by": 1
                            }).eq(pk_column, record_id).execute()
                            cleared_count += 1
                        except Exception as e:
                            print(f"  Warning: Could not delete {table} record {record_id}: {e}")
        except Exception as e:
            print(f"  Note: Could not clear {table}: {e}")
            # Continue with other tables
    
    print(f"[OK] Cleared {cleared_count} existing records (soft deleted)")
    return True


def create_schema():
    """Display instructions for creating database schema"""
    print("Creating database schema...")
    print("[NOTE] Please run database/schema.sql in your Supabase SQL Editor")
    print("   Go to: Supabase Dashboard > SQL Editor > New Query")
    print("   Copy and paste the contents of database/schema.sql")
    return True


def populate_users(user_id=None):
    """Populate Users table with default admin user"""
    print("Populating Users table...")
    
    supabase = get_client()
    
    # Check if default user already exists
    existing_user = supabase.table("users").select("user_id").eq("username", "admin").execute()
    
    if existing_user.data:
        print("[OK] Default admin user already exists")
        return existing_user.data[0]["user_id"]
    
    user_data = {
        "username": "admin",
        "email": "admin@munnasuprathik.in",
        "full_name": "System Administrator",
        "role": "admin",
        "is_active": True
    }
    
    try:
        result = supabase.table("users").insert(user_data).execute()
        user_id = result.data[0]["user_id"]
        print(f"[OK] Created default admin user (ID: {user_id})")
        return user_id
    except Exception as e:
        print(f"Error creating admin user: {e}")
        return None


def populate_stops(user_id=None):
    """Populate Stops table with extensive Bengaluru locations"""
    print("Populating Stops table with Bengaluru locations...")
    supabase = get_client()
    
    # Extensive list of real Bengaluru locations with accurate coordinates
    stops_data = [
        # Central Bangalore
        {"name": "Majestic Bus Stand", "latitude": 12.9774, "longitude": 77.5711, "description": "Central bus terminal", "address": "Majestic, Bangalore 560023", "is_active": True, "created_by": user_id, "updated_by": user_id},
        {"name": "Kempegowda Bus Station", "latitude": 12.9784, "longitude": 77.5689, "description": "Main bus station", "address": "Kempegowda Bus Station, Bangalore 560023", "is_active": True, "created_by": user_id, "updated_by": user_id},
        {"name": "MG Road", "latitude": 12.9716, "longitude": 77.5946, "description": "Commercial hub", "address": "MG Road, Bangalore 560001", "is_active": True, "created_by": user_id, "updated_by": user_id},
        {"name": "Brigade Road", "latitude": 12.9730, "longitude": 77.6080, "description": "Shopping and entertainment", "address": "Brigade Road, Bangalore 560001", "is_active": True, "created_by": user_id, "updated_by": user_id},
        {"name": "Cubbon Park", "latitude": 12.9764, "longitude": 77.5928, "description": "Central park area", "address": "Cubbon Park, Bangalore 560001", "is_active": True, "created_by": user_id, "updated_by": user_id},
        {"name": "Vidhana Soudha", "latitude": 12.9794, "longitude": 77.5908, "description": "Government building area", "address": "Vidhana Soudha, Bangalore 560001", "is_active": True, "created_by": user_id, "updated_by": user_id},
        
        # South Bangalore - IT Corridor
        {"name": "Electronic City", "latitude": 12.8456, "longitude": 77.6633, "description": "Major IT park", "address": "Electronic City, Bangalore 560100", "is_active": True, "created_by": user_id, "updated_by": user_id},
        {"name": "HSR Layout", "latitude": 12.9120, "longitude": 77.6446, "description": "Residential and IT area", "address": "HSR Layout, Bangalore 560102", "is_active": True, "created_by": user_id, "updated_by": user_id},
        {"name": "Koramangala", "latitude": 12.9352, "longitude": 77.6245, "description": "Residential and commercial hub", "address": "Koramangala, Bangalore 560095", "is_active": True, "created_by": user_id, "updated_by": user_id},
        {"name": "BTM Layout", "latitude": 12.9167, "longitude": 77.6167, "description": "Residential area", "address": "BTM Layout, Bangalore 560076", "is_active": True, "created_by": user_id, "updated_by": user_id},
        {"name": "Bommanahalli", "latitude": 12.9000, "longitude": 77.6333, "description": "Industrial and residential", "address": "Bommanahalli, Bangalore 560068", "is_active": True, "created_by": user_id, "updated_by": user_id},
        {"name": "Silk Board", "latitude": 12.9150, "longitude": 77.6250, "description": "Major junction", "address": "Silk Board Junction, Bangalore 560068", "is_active": True, "created_by": user_id, "updated_by": user_id},
        
        # East Bangalore
        {"name": "Whitefield", "latitude": 12.9698, "longitude": 77.7499, "description": "IT hub and residential", "address": "Whitefield, Bangalore 560066", "is_active": True, "created_by": user_id, "updated_by": user_id},
        {"name": "Marathahalli", "latitude": 12.9583, "longitude": 77.7000, "description": "IT corridor", "address": "Marathahalli, Bangalore 560037", "is_active": True, "created_by": user_id, "updated_by": user_id},
        {"name": "KR Puram", "latitude": 13.0083, "longitude": 77.7000, "description": "Residential and commercial", "address": "KR Puram, Bangalore 560036", "is_active": True, "created_by": user_id, "updated_by": user_id},
        {"name": "Indiranagar", "latitude": 12.9784, "longitude": 77.6408, "description": "Upscale residential area", "address": "Indiranagar, Bangalore 560038", "is_active": True, "created_by": user_id, "updated_by": user_id},
        {"name": "CV Raman Nagar", "latitude": 12.9833, "longitude": 77.6500, "description": "Residential area", "address": "CV Raman Nagar, Bangalore 560093", "is_active": True, "created_by": user_id, "updated_by": user_id},
        {"name": "Banaswadi", "latitude": 13.0167, "longitude": 77.6500, "description": "Residential locality", "address": "Banaswadi, Bangalore 560043", "is_active": True, "created_by": user_id, "updated_by": user_id},
        
        # North Bangalore
        {"name": "Peenya Industrial Area", "latitude": 13.0251, "longitude": 77.5173, "description": "Major industrial hub", "address": "Peenya, Bangalore 560058", "is_active": True, "created_by": user_id, "updated_by": user_id},
        {"name": "Yeshwanthpur", "latitude": 13.0250, "longitude": 77.5417, "description": "Commercial and residential", "address": "Yeshwanthpur, Bangalore 560022", "is_active": True, "created_by": user_id, "updated_by": user_id},
        {"name": "Malleswaram", "latitude": 12.9917, "longitude": 77.5708, "description": "Traditional residential area", "address": "Malleswaram, Bangalore 560003", "is_active": True, "created_by": user_id, "updated_by": user_id},
        {"name": "Rajajinagar", "latitude": 12.9833, "longitude": 77.5500, "description": "Residential and commercial", "address": "Rajajinagar, Bangalore 560010", "is_active": True, "created_by": user_id, "updated_by": user_id},
        {"name": "Vijayanagar", "latitude": 12.9750, "longitude": 77.5250, "description": "Residential area", "address": "Vijayanagar, Bangalore 560040", "is_active": True, "created_by": user_id, "updated_by": user_id},
        {"name": "Nagarbhavi", "latitude": 12.9500, "longitude": 77.5083, "description": "Residential locality", "address": "Nagarbhavi, Bangalore 560072", "is_active": True, "created_by": user_id, "updated_by": user_id},
        
        # West Bangalore
        {"name": "Gavipuram", "latitude": 12.9352, "longitude": 77.5500, "description": "Residential area", "address": "Gavipuram, Bangalore 560019", "is_active": True, "created_by": user_id, "updated_by": user_id},
        {"name": "Basavanagudi", "latitude": 12.9417, "longitude": 77.5708, "description": "Traditional area", "address": "Basavanagudi, Bangalore 560004", "is_active": True, "created_by": user_id, "updated_by": user_id},
        {"name": "Jayanagar", "latitude": 12.9333, "longitude": 77.5833, "description": "Residential and commercial", "address": "Jayanagar, Bangalore 560011", "is_active": True, "created_by": user_id, "updated_by": user_id},
        {"name": "JP Nagar", "latitude": 12.9083, "longitude": 77.5833, "description": "Residential area", "address": "JP Nagar, Bangalore 560078", "is_active": True, "created_by": user_id, "updated_by": user_id},
        {"name": "Banashankari", "latitude": 12.9250, "longitude": 77.5500, "description": "Residential locality", "address": "Banashankari, Bangalore 560085", "is_active": True, "created_by": user_id, "updated_by": user_id},
        {"name": "Uttarahalli", "latitude": 12.9000, "longitude": 77.5417, "description": "Residential area", "address": "Uttarahalli, Bangalore 560061", "is_active": True, "created_by": user_id, "updated_by": user_id},
        
        # Outer Areas
        {"name": "Hebbal", "latitude": 13.0417, "longitude": 77.5917, "description": "Residential and IT", "address": "Hebbal, Bangalore 560024", "is_active": True, "created_by": user_id, "updated_by": user_id},
        {"name": "Yelahanka", "latitude": 13.1000, "longitude": 77.5917, "description": "Residential area", "address": "Yelahanka, Bangalore 560064", "is_active": True, "created_by": user_id, "updated_by": user_id},
        {"name": "Bellandur", "latitude": 12.9250, "longitude": 77.6750, "description": "IT corridor", "address": "Bellandur, Bangalore 560103", "is_active": True, "created_by": user_id, "updated_by": user_id},
        {"name": "Sarjapur", "latitude": 12.8917, "longitude": 77.7750, "description": "IT and residential", "address": "Sarjapur, Bangalore 560035", "is_active": True, "created_by": user_id, "updated_by": user_id},
        {"name": "Hosur Road", "latitude": 12.8583, "longitude": 77.6417, "description": "Highway junction", "address": "Hosur Road, Bangalore 560068", "is_active": True, "created_by": user_id, "updated_by": user_id},
    ]
    
    inserted_count = 0
    for stop in stops_data:
        try:
            supabase.table("stops").insert(stop).execute()
            inserted_count += 1
        except Exception as e:
            print(f"Error inserting stop {stop['name']}: {e}")
    
    print(f"[OK] Inserted {inserted_count} Bengaluru stops")
    return inserted_count


def populate_paths(user_id=None):
    """Populate Paths table with Bengaluru routes"""
    print("Populating Paths table with Bengaluru routes...")
    supabase = get_client()
    
    # Get all stops
    stops_response = supabase.table("stops").select("stop_id, name").is_("deleted_at", "null").execute()
    stops = {stop["name"]: stop["stop_id"] for stop in stops_response.data}
    
    # Create realistic Bengaluru paths with professional naming conventions
    paths_data = [
        {
            "path_name": "PATH-EC-001: Electronic City Express",
            "ordered_list_of_stop_ids": [stops["Electronic City"], stops["Hosur Road"], stops["BTM Layout"], stops["Silk Board"], stops["HSR Layout"], stops["Koramangala"], stops["Indiranagar"]],
            "description": "Express route connecting Electronic City IT hub to Indiranagar via major tech corridors",
            "total_distance_km": 32.5,
            "estimated_duration_minutes": 65,
            "is_active": True,
            "created_by": user_id,
            "updated_by": user_id
        },
        {
            "path_name": "PATH-CW-002: Central to Whitefield",
            "ordered_list_of_stop_ids": [stops["Majestic Bus Stand"], stops["Kempegowda Bus Station"], stops["MG Road"], stops["Indiranagar"], stops["Marathahalli"], stops["Whitefield"]],
            "description": "Primary route from city center (Majestic) to Whitefield IT hub",
            "total_distance_km": 35.2,
            "estimated_duration_minutes": 70,
            "is_active": True,
            "created_by": user_id,
            "updated_by": user_id
        },
        {
            "path_name": "PATH-NS-003: North-South Corridor",
            "ordered_list_of_stop_ids": [stops["Yeshwanthpur"], stops["Malleswaram"], stops["Vidhana Soudha"], stops["Cubbon Park"], stops["Jayanagar"], stops["JP Nagar"], stops["Banashankari"]],
            "description": "North to South Bangalore arterial route connecting residential and commercial zones",
            "total_distance_km": 22.8,
            "estimated_duration_minutes": 55,
            "is_active": True,
            "created_by": user_id,
            "updated_by": user_id
        },
        {
            "path_name": "PATH-IB-004: Industrial Belt Route",
            "ordered_list_of_stop_ids": [stops["Peenya Industrial Area"], stops["Yeshwanthpur"], stops["Rajajinagar"], stops["Vijayanagar"], stops["Nagarbhavi"]],
            "description": "Route serving major industrial and manufacturing areas in North-West Bangalore",
            "total_distance_km": 18.5,
            "estimated_duration_minutes": 42,
            "is_active": True,
            "created_by": user_id,
            "updated_by": user_id
        },
        {
            "path_name": "PATH-EW-005: East-West Tech Circuit",
            "ordered_list_of_stop_ids": [stops["Whitefield"], stops["KR Puram"], stops["Marathahalli"], stops["Bellandur"], stops["HSR Layout"], stops["Koramangala"], stops["BTM Layout"]],
            "description": "Circular route connecting all major IT parks and tech corridors",
            "total_distance_km": 42.3,
            "estimated_duration_minutes": 85,
            "is_active": True,
            "created_by": user_id,
            "updated_by": user_id
        },
        {
            "path_name": "PATH-AR-006: Airport Road Express",
            "ordered_list_of_stop_ids": [stops["Yelahanka"], stops["Hebbal"], stops["Yeshwanthpur"], stops["Malleswaram"], stops["MG Road"], stops["Brigade Road"]],
            "description": "Express route from airport area (Yelahanka) to city center commercial district",
            "total_distance_km": 28.7,
            "estimated_duration_minutes": 58,
            "is_active": True,
            "created_by": user_id,
            "updated_by": user_id
        },
        {
            "path_name": "PATH-OR-007: Outer Ring Road",
            "ordered_list_of_stop_ids": [stops["Sarjapur"], stops["Bellandur"], stops["HSR Layout"], stops["Bommanahalli"], stops["BTM Layout"], stops["Jayanagar"]],
            "description": "Outer ring road route connecting peripheral residential and IT areas",
            "total_distance_km": 38.5,
            "estimated_duration_minutes": 75,
            "is_active": True,
            "created_by": user_id,
            "updated_by": user_id
        },
        {
            "path_name": "PATH-HR-008: Heritage Route",
            "ordered_list_of_stop_ids": [stops["Basavanagudi"], stops["Gavipuram"], stops["Jayanagar"], stops["BTM Layout"], stops["Bommanahalli"]],
            "description": "Route through traditional and heritage areas of South Bangalore",
            "total_distance_km": 15.8,
            "estimated_duration_minutes": 38,
            "is_active": True,
            "created_by": user_id,
            "updated_by": user_id
        },
        {
            "path_name": "PATH-RC-009: Residential Connector",
            "ordered_list_of_stop_ids": [stops["Banaswadi"], stops["CV Raman Nagar"], stops["Indiranagar"], stops["Koramangala"], stops["HSR Layout"]],
            "description": "Route connecting major residential neighborhoods in East and South-East Bangalore",
            "total_distance_km": 19.2,
            "estimated_duration_minutes": 45,
            "is_active": True,
            "created_by": user_id,
            "updated_by": user_id
        },
        {
            "path_name": "PATH-CH-010: Commercial Hub Route",
            "ordered_list_of_stop_ids": [stops["Brigade Road"], stops["MG Road"], stops["Cubbon Park"], stops["Vidhana Soudha"], stops["Kempegowda Bus Station"]],
            "description": "Route through central business district and commercial hubs",
            "total_distance_km": 9.5,
            "estimated_duration_minutes": 25,
            "is_active": True,
            "created_by": user_id,
            "updated_by": user_id
        },
        {
            "path_name": "PATH-TP-011: Tech Park Shuttle",
            "ordered_list_of_stop_ids": [stops["Electronic City"], stops["Hosur Road"], stops["BTM Layout"], stops["Silk Board"], stops["HSR Layout"], stops["Bellandur"]],
            "description": "Dedicated shuttle service connecting major tech parks and IT corridors",
            "total_distance_km": 28.3,
            "estimated_duration_minutes": 60,
            "is_active": True,
            "created_by": user_id,
            "updated_by": user_id
        },
        {
            "path_name": "PATH-NE-012: North Extension",
            "ordered_list_of_stop_ids": [stops["Yelahanka"], stops["Hebbal"], stops["Yeshwanthpur"], stops["Peenya Industrial Area"], stops["Rajajinagar"]],
            "description": "Northern extension route serving airport area and industrial zones",
            "total_distance_km": 32.4,
            "estimated_duration_minutes": 65,
            "is_active": True,
            "created_by": user_id,
            "updated_by": user_id
        },
    ]
    
    inserted_count = 0
    for path in paths_data:
        try:
            supabase.table("paths").insert(path).execute()
            inserted_count += 1
        except Exception as e:
            print(f"Error inserting path {path['path_name']}: {e}")
    
    print(f"[OK] Inserted {inserted_count} Bengaluru paths")
    return inserted_count


def populate_routes(user_id=None):
    """Populate Routes table with Bengaluru routes"""
    print("Populating Routes table...")
    supabase = get_client()
    
    # Get paths
    paths_response = supabase.table("paths").select("path_id, path_name").is_("deleted_at", "null").execute()
    paths = {path["path_name"]: path["path_id"] for path in paths_response.data}
    
    # Get stops for start/end points
    stops_response = supabase.table("stops").select("stop_id, name").is_("deleted_at", "null").execute()
    stops = {stop["name"]: stop["stop_id"] for stop in stops_response.data}
    
    # Create multiple routes for each path with different times
    routes_data = []
    
    # Morning routes (6 AM - 10 AM)
    morning_times = ["06:00:00", "06:30:00", "07:00:00", "07:30:00", "08:00:00", "08:30:00", "09:00:00", "09:30:00", "10:00:00"]
    # Afternoon routes (12 PM - 3 PM)
    afternoon_times = ["12:00:00", "12:30:00", "13:00:00", "13:30:00", "14:00:00", "14:30:00", "15:00:00"]
    # Evening routes (5 PM - 9 PM)
    evening_times = ["17:00:00", "17:30:00", "18:00:00", "18:30:00", "19:00:00", "19:30:00", "20:00:00", "20:30:00", "21:00:00"]
    # Night routes (10 PM - 1 AM)
    night_times = ["22:00:00", "22:30:00", "23:00:00", "23:30:00", "00:00:00", "00:30:00", "01:00:00"]
    
    # Professional route naming with shift indicators
    # Reduced to 12 paths (60% of 20) for better performance
    path_route_mapping = [
        ("PATH-EC-001: Electronic City Express", "Electronic City", "Indiranagar", "Forward"),
        ("PATH-CW-002: Central to Whitefield", "Majestic Bus Stand", "Whitefield", "Forward"),
        ("PATH-NS-003: North-South Corridor", "Yeshwanthpur", "Banashankari", "Forward"),
        ("PATH-IB-004: Industrial Belt Route", "Peenya Industrial Area", "Nagarbhavi", "Forward"),
        ("PATH-EW-005: East-West Tech Circuit", "Whitefield", "BTM Layout", "Circular"),
        ("PATH-AR-006: Airport Road Express", "Yelahanka", "Brigade Road", "Forward"),
        ("PATH-OR-007: Outer Ring Road", "Sarjapur", "Jayanagar", "Forward"),
        ("PATH-HR-008: Heritage Route", "Basavanagudi", "Bommanahalli", "Forward"),
        ("PATH-RC-009: Residential Connector", "Banaswadi", "HSR Layout", "Forward"),
        ("PATH-CH-010: Commercial Hub Route", "Brigade Road", "Kempegowda Bus Station", "Forward"),
        ("PATH-TP-011: Tech Park Shuttle", "Electronic City", "Bellandur", "Forward"),
        ("PATH-NE-012: North Extension", "Yelahanka", "Rajajinagar", "Forward"),
    ]
    
    # Create routes with professional naming: ROUTE-[PATH_CODE]-[SHIFT]-[TIME]
    shift_names = {
        "06:00:00": "MORN", "06:30:00": "MORN", "07:00:00": "MORN", "07:30:00": "MORN", "08:00:00": "MORN",
        "12:00:00": "NOON", "12:30:00": "NOON", "13:00:00": "NOON", "13:30:00": "NOON", "14:00:00": "NOON",
        "17:00:00": "EVE", "17:30:00": "EVE", "18:00:00": "EVE", "18:30:00": "EVE", "19:00:00": "EVE",
        "22:00:00": "NITE", "22:30:00": "NITE", "23:00:00": "NITE", "23:30:00": "NITE", "00:00:00": "NITE",
    }
    
    route_counter = 1
    for path_name, start_point, end_point, direction in path_route_mapping:
        if path_name not in paths:
            continue
        
        # Extract path code and description from path name
        # e.g., "PATH-EC-001: Electronic City Express" -> code="EC-001", desc="Electronic City Express"
        if ": " in path_name:
            path_code = path_name.split(":")[0].replace("PATH-", "")
            path_description = path_name.split(": ")[1]
        else:
            path_code = path_name.replace("PATH-", "")
            path_description = path_name
        
        # Create routes for different times (4 routes per path: Morning, Noon, Evening, Night)
        selected_times = [
            morning_times[4],  # 08:00
            afternoon_times[2],  # 13:00
            evening_times[4],  # 19:00
            night_times[4],  # 00:00
        ]
        
        for shift_time in selected_times:
            shift_code = shift_names.get(shift_time, "REG")
            time_str = shift_time[:5].replace(":", "")
            route_code = f"ROUTE-{path_code}-{shift_code}-{time_str}"
            
            # Professional route display name
            route_display_name = f"{route_code}: {path_description}"
            
            routes_data.append({
                "path_id": paths[path_name],
                "route_display_name": route_display_name,
                "shift_time": shift_time,
                "direction": direction,
                "start_point": start_point,
                "end_point": end_point,
                "status": "active",
                "notes": f"Bengaluru route - {path_name} - {shift_code} shift ({shift_time[:5]})",
                "created_by": user_id,
                "updated_by": user_id
            })
            route_counter += 1
    
    inserted_count = 0
    for route in routes_data:
        try:
            supabase.table("routes").insert(route).execute()
            inserted_count += 1
        except Exception as e:
            print(f"Error inserting route {route['route_display_name']}: {e}")
    
    print(f"[OK] Inserted {inserted_count} Bengaluru routes")
    return inserted_count


def populate_vehicles(user_id=None):
    """Populate Vehicles table with Bengaluru vehicles"""
    print("Populating Vehicles table...")
    supabase = get_client()
    
    vehicles_data = [
        # Premium Buses
        {"license_plate": "KA-01-AB-1234", "type": "Bus", "capacity": 50, "make": "Tata", "model": "Starbus Ultra", "year": 2023, "color": "Blue", "is_available": True, "status": "active", "created_by": user_id, "updated_by": user_id},
        {"license_plate": "KA-01-CD-5678", "type": "Bus", "capacity": 45, "make": "Ashok Leyland", "model": "Viking BS6", "year": 2022, "color": "Red", "is_available": True, "status": "active", "created_by": user_id, "updated_by": user_id},
        {"license_plate": "KA-01-EF-9012", "type": "Bus", "capacity": 40, "make": "Volvo", "model": "9400 Multi-Axle", "year": 2021, "color": "White", "is_available": True, "status": "active", "created_by": user_id, "updated_by": user_id},
        {"license_plate": "KA-01-GH-3456", "type": "Bus", "capacity": 35, "make": "Tata", "model": "Marcopolo Executive", "year": 2022, "color": "Green", "is_available": True, "status": "active", "created_by": user_id, "updated_by": user_id},
        {"license_plate": "KA-02-IJ-7890", "type": "Bus", "capacity": 48, "make": "Ashok Leyland", "model": "Janbus AC", "year": 2023, "color": "Yellow", "is_available": True, "status": "active", "created_by": user_id, "updated_by": user_id},
        {"license_plate": "KA-02-KL-2345", "type": "Bus", "capacity": 42, "make": "Tata", "model": "Ultra 1518", "year": 2022, "color": "Orange", "is_available": True, "status": "active", "created_by": user_id, "updated_by": user_id},
        {"license_plate": "KA-02-MN-6789", "type": "Bus", "capacity": 38, "make": "Volvo", "model": "8400 Xpress", "year": 2021, "color": "Silver", "is_available": True, "status": "active", "created_by": user_id, "updated_by": user_id},
        {"license_plate": "KA-03-OP-0123", "type": "Bus", "capacity": 44, "make": "Ashok Leyland", "model": "Dost Plus", "year": 2022, "color": "Maroon", "is_available": True, "status": "active", "created_by": user_id, "updated_by": user_id},
        {"license_plate": "KA-03-QR-4567", "type": "Bus", "capacity": 36, "make": "Tata", "model": "LPO 1613", "year": 2021, "color": "Navy Blue", "is_available": True, "status": "active", "created_by": user_id, "updated_by": user_id},
        {"license_plate": "KA-03-ST-8901", "type": "Bus", "capacity": 46, "make": "Volvo", "model": "B7R Multi-Axle", "year": 2023, "color": "White", "is_available": True, "status": "active", "created_by": user_id, "updated_by": user_id},
        {"license_plate": "KA-04-UV-2345", "type": "Bus", "capacity": 50, "make": "Tata", "model": "Starbus Hybrid", "year": 2023, "color": "Blue", "is_available": True, "status": "active", "created_by": user_id, "updated_by": user_id},
        {"license_plate": "KA-04-WX-5678", "type": "Bus", "capacity": 43, "make": "Ashok Leyland", "model": "Viking Electric", "year": 2023, "color": "Green", "is_available": True, "status": "active", "created_by": user_id, "updated_by": user_id},
        {"license_plate": "KA-05-YZ-9012", "type": "Bus", "capacity": 39, "make": "Volvo", "model": "9400 XL", "year": 2022, "color": "Silver", "is_available": True, "status": "active", "created_by": user_id, "updated_by": user_id},
        {"license_plate": "KA-05-AA-3456", "type": "Bus", "capacity": 41, "make": "Tata", "model": "Ultra 1518 AC", "year": 2022, "color": "Red", "is_available": True, "status": "active", "created_by": user_id, "updated_by": user_id},
        {"license_plate": "KA-05-BB-7890", "type": "Bus", "capacity": 37, "make": "Ashok Leyland", "model": "Janbus Premium", "year": 2023, "color": "White", "is_available": True, "status": "active", "created_by": user_id, "updated_by": user_id},
        
        # Premium Cabs
        {"license_plate": "KA-06-CC-1234", "type": "Cab", "capacity": 6, "make": "Toyota", "model": "Innova Crysta", "year": 2023, "color": "Silver", "is_available": True, "status": "active", "created_by": user_id, "updated_by": user_id},
        {"license_plate": "KA-06-DD-5678", "type": "Cab", "capacity": 7, "make": "Toyota", "model": "Innova HyCross", "year": 2023, "color": "White", "is_available": True, "status": "active", "created_by": user_id, "updated_by": user_id},
        {"license_plate": "KA-07-EE-9012", "type": "Cab", "capacity": 6, "make": "Mahindra", "model": "XUV700", "year": 2023, "color": "Black", "is_available": True, "status": "active", "created_by": user_id, "updated_by": user_id},
        {"license_plate": "KA-07-FF-3456", "type": "Cab", "capacity": 6, "make": "Toyota", "model": "Innova Crysta ZX", "year": 2022, "color": "Grey", "is_available": True, "status": "active", "created_by": user_id, "updated_by": user_id},
        {"license_plate": "KA-08-GG-7890", "type": "Cab", "capacity": 7, "make": "Maruti", "model": "Ertiga Tour", "year": 2022, "color": "Blue", "is_available": True, "status": "active", "created_by": user_id, "updated_by": user_id},
        {"license_plate": "KA-08-HH-2345", "type": "Cab", "capacity": 6, "make": "Toyota", "model": "Innova", "year": 2021, "color": "Red", "is_available": True, "status": "active", "created_by": user_id, "updated_by": user_id},
        {"license_plate": "KA-09-II-6789", "type": "Cab", "capacity": 7, "make": "Mahindra", "model": "Xylo D4", "year": 2021, "color": "White", "is_available": True, "status": "active", "created_by": user_id, "updated_by": user_id},
        {"license_plate": "KA-09-JJ-0123", "type": "Cab", "capacity": 6, "make": "Toyota", "model": "Innova Crysta VX", "year": 2022, "color": "Silver", "is_available": True, "status": "active", "created_by": user_id, "updated_by": user_id},
    ]
    
    inserted_count = 0
    for vehicle in vehicles_data:
        try:
            supabase.table("vehicles").insert(vehicle).execute()
            inserted_count += 1
        except Exception as e:
            print(f"Error inserting vehicle {vehicle['license_plate']}: {e}")
    
    print(f"[OK] Inserted {inserted_count} Bengaluru vehicles")
    return inserted_count


def populate_drivers(user_id=None):
    """Populate Drivers table with Bengaluru drivers"""
    print("Populating Drivers table...")
    supabase = get_client()
    
    drivers_data = [
        {"name": "Amit Kumar", "phone_number": "+91-9876543210", "email": "amit.kumar@munnasuprathik.in", "license_number": "KA-01-2020-123456", "is_available": True, "status": "active", "created_by": user_id, "updated_by": user_id},
        {"name": "Rajesh Reddy", "phone_number": "+91-9876543211", "email": "rajesh.reddy@munnasuprathik.in", "license_number": "KA-01-2019-234567", "is_available": True, "status": "active", "created_by": user_id, "updated_by": user_id},
        {"name": "Kumar Swamy", "phone_number": "+91-9876543212", "email": "kumar.swamy@munnasuprathik.in", "license_number": "KA-02-2021-345678", "is_available": True, "status": "active", "created_by": user_id, "updated_by": user_id},
        {"name": "Suresh Naidu", "phone_number": "+91-9876543213", "email": "suresh.naidu@munnasuprathik.in", "license_number": "KA-02-2020-456789", "is_available": True, "status": "active", "created_by": user_id, "updated_by": user_id},
        {"name": "Ramesh Iyer", "phone_number": "+91-9876543214", "email": "ramesh.iyer@munnasuprathik.in", "license_number": "KA-03-2019-567890", "is_available": True, "status": "active", "created_by": user_id, "updated_by": user_id},
        {"name": "Vikram Singh", "phone_number": "+91-9876543215", "email": "vikram.singh@munnasuprathik.in", "license_number": "KA-03-2021-678901", "is_available": True, "status": "active", "created_by": user_id, "updated_by": user_id},
        {"name": "Prakash Rao", "phone_number": "+91-9876543216", "email": "prakash.rao@munnasuprathik.in", "license_number": "KA-04-2020-789012", "is_available": True, "status": "active", "created_by": user_id, "updated_by": user_id},
        {"name": "Mohan Das", "phone_number": "+91-9876543217", "email": "mohan.das@munnasuprathik.in", "license_number": "KA-04-2019-890123", "is_available": True, "status": "active", "created_by": user_id, "updated_by": user_id},
        {"name": "Naveen Kumar", "phone_number": "+91-9876543218", "email": "naveen.kumar@munnasuprathik.in", "license_number": "KA-05-2022-901234", "is_available": True, "status": "active", "created_by": user_id, "updated_by": user_id},
        {"name": "Srinivas Murthy", "phone_number": "+91-9876543219", "email": "srinivas.murthy@munnasuprathik.in", "license_number": "KA-05-2021-012345", "is_available": True, "status": "active", "created_by": user_id, "updated_by": user_id},
        {"name": "Anil Shetty", "phone_number": "+91-9876543220", "email": "anil.shetty@munnasuprathik.in", "license_number": "KA-01-2020-123457", "is_available": True, "status": "active", "created_by": user_id, "updated_by": user_id},
        {"name": "Deepak Joshi", "phone_number": "+91-9876543221", "email": "deepak.joshi@munnasuprathik.in", "license_number": "KA-01-2019-234568", "is_available": True, "status": "active", "created_by": user_id, "updated_by": user_id},
        {"name": "Ganesh Patil", "phone_number": "+91-9876543222", "email": "ganesh.patil@munnasuprathik.in", "license_number": "KA-02-2021-345679", "is_available": True, "status": "active", "created_by": user_id, "updated_by": user_id},
        {"name": "Harish Nair", "phone_number": "+91-9876543223", "email": "harish.nair@munnasuprathik.in", "license_number": "KA-02-2020-456790", "is_available": True, "status": "active", "created_by": user_id, "updated_by": user_id},
        {"name": "Ishwar Prasad", "phone_number": "+91-9876543224", "email": "ishwar.prasad@munnasuprathik.in", "license_number": "KA-03-2019-567891", "is_available": True, "status": "active", "created_by": user_id, "updated_by": user_id},
        {"name": "Jagadish Kumar", "phone_number": "+91-9876543225", "email": "jagadish.kumar@munnasuprathik.in", "license_number": "KA-03-2021-678902", "is_available": True, "status": "active", "created_by": user_id, "updated_by": user_id},
        {"name": "Kiran Shetty", "phone_number": "+91-9876543226", "email": "kiran.shetty@munnasuprathik.in", "license_number": "KA-04-2020-789013", "is_available": True, "status": "active", "created_by": user_id, "updated_by": user_id},
        {"name": "Lokesh Reddy", "phone_number": "+91-9876543227", "email": "lokesh.reddy@munnasuprathik.in", "license_number": "KA-04-2019-890124", "is_available": True, "status": "active", "created_by": user_id, "updated_by": user_id},
        {"name": "Manjunath Swamy", "phone_number": "+91-9876543228", "email": "manjunath.swamy@munnasuprathik.in", "license_number": "KA-05-2022-901235", "is_available": True, "status": "active", "created_by": user_id, "updated_by": user_id},
        {"name": "Nagesh Iyer", "phone_number": "+91-9876543229", "email": "nagesh.iyer@munnasuprathik.in", "license_number": "KA-05-2021-012346", "is_available": True, "status": "active", "created_by": user_id, "updated_by": user_id},
    ]
    
    inserted_count = 0
    for driver in drivers_data:
        try:
            supabase.table("drivers").insert(driver).execute()
            inserted_count += 1
        except Exception as e:
            print(f"Error inserting driver {driver['name']}: {e}")
    
    print(f"[OK] Inserted {inserted_count} Bengaluru drivers")
    return inserted_count


def populate_daily_trips(user_id=None):
    """Populate DailyTrips table with Bengaluru trips"""
    print("Populating DailyTrips table...")
    supabase = get_client()
    
    # Get routes
    routes_response = supabase.table("routes").select("route_id, route_display_name").is_("deleted_at", "null").execute()
    routes = {route["route_display_name"]: route["route_id"] for route in routes_response.data}
    
    # Create trips for today and next 4 days (reduced to 60% - was 7 days)
    today = date.today()
    trip_dates = [today + timedelta(days=i) for i in range(4)]  # 4 days of trips (60% of 7)
    
    trips_data = []
    statuses = ["scheduled", "in_progress", "completed", "scheduled", "scheduled"]
    booking_percentages = [15.0, 25.0, 35.0, 45.0, 55.0, 65.0, 75.0, 85.0, 95.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0]
    live_statuses = ["IN", "OUT", "DELAYED", "ON TIME", "DEPARTED", "ARRIVED"]
    
    route_index = 0
    for route_name, route_id in routes.items():
        # Extract route code for better trip naming
        route_code = route_name.split(":")[0] if ":" in route_name else f"ROUTE-{route_index+1:03d}"
        
        for trip_date in trip_dates:
            booking_pct = booking_percentages[route_index % len(booking_percentages)]
            total_bookings = int((booking_pct / 100) * 45)  # Assuming 45 capacity average
            status = statuses[route_index % len(statuses)]
            live_status_code = live_statuses[route_index % len(live_statuses)]
            
            # Professional trip naming: TRIP-[ROUTE_CODE]-[DATE]
            date_str = trip_date.strftime('%d%m%Y')
            trip_display_name = f"{route_code}-{date_str}"
            
            # Extract time from route name for live status
            time_from_route = route_name.split("-")[-1] if "-" in route_name else "0800"
            live_status = f"{time_from_route[:2]}:{time_from_route[2:4]} {live_status_code}"
            
            trips_data.append({
                "route_id": route_id,
                "display_name": trip_display_name,
                "trip_date": str(trip_date),
                "booking_status_percentage": booking_pct,
                "live_status": live_status,
                "total_bookings": total_bookings,
                "status": status,
                "notes": f"Bengaluru trip - {route_name} - {trip_date.strftime('%d-%m-%Y')}",
                "created_by": user_id,
                "updated_by": user_id
            })
        route_index += 1
    
    inserted_count = 0
    for trip in trips_data:
        try:
            supabase.table("daily_trips").insert(trip).execute()
            inserted_count += 1
        except Exception as e:
            print(f"Error inserting trip {trip['display_name']}: {e}")
    
    print(f"[OK] Inserted {inserted_count} Bengaluru trips")
    return inserted_count


def populate_deployments(user_id=None):
    """Populate Deployments table"""
    print("Populating Deployments table...")
    supabase = get_client()
    
    # Get trips
    trips_response = supabase.table("daily_trips").select("trip_id, display_name").is_("deleted_at", "null").execute()
    trips = {trip["display_name"]: trip["trip_id"] for trip in trips_response.data}
    
    # Get vehicles
    vehicles_response = supabase.table("vehicles").select("vehicle_id, license_plate").is_("deleted_at", "null").execute()
    vehicles = {vehicle["license_plate"]: vehicle["vehicle_id"] for vehicle in vehicles_response.data}
    
    # Get drivers
    drivers_response = supabase.table("drivers").select("driver_id, name").is_("deleted_at", "null").execute()
    drivers = {driver["name"]: driver["driver_id"] for driver in drivers_response.data}
    
    deployments_data = []
    deployment_statuses = ["assigned", "confirmed", "in_transit", "completed"]
    
    vehicle_list = list(vehicles.values())
    driver_list = list(drivers.values())
    
    trip_index = 0
    # Deploy more trips (up to 50% of available trips)
    max_deployments = min(len(trips), len(vehicle_list) * 2, len(driver_list) * 2)
    
    for trip_name, trip_id in list(trips.items())[:max_deployments]:
        vehicle_id = vehicle_list[trip_index % len(vehicle_list)]
        driver_id = driver_list[trip_index % len(driver_list)]
        status = deployment_statuses[trip_index % len(deployment_statuses)]
        
        deployments_data.append({
            "trip_id": trip_id,
            "vehicle_id": vehicle_id,
            "driver_id": driver_id,
            "deployment_status": status,
            "created_by": user_id,
            "updated_by": user_id
        })
        trip_index += 1
    
    inserted_count = 0
    for deployment in deployments_data:
        try:
            supabase.table("deployments").insert(deployment).execute()
            inserted_count += 1
        except Exception as e:
            print(f"Error inserting deployment: {e}")
    
    print(f"[OK] Inserted {inserted_count} deployments")
    return inserted_count


def main():
    """Main function to initialize database"""
    print("=" * 60)
    print("Movi Database Initialization - Bengaluru Transport System")
    print("=" * 60)
    print()
    
    # Step 1: Create schema (user needs to run SQL manually)
    create_schema()
    print()
    
    # Wait for user confirmation
    input("Press Enter after you've run the schema.sql file in Supabase SQL Editor...")
    print()
    
    # Step 1.5: Clear existing data
    clear_choice = input("Do you want to clear existing data before populating? (y/n): ").strip().lower()
    if clear_choice == 'y':
        clear_existing_data()
        print()
    
    # Step 2: Create default admin user first
    user_id = populate_users()
    print()
    
    # Step 3: Populate tables with extensive Bengaluru data
    try:
        stops_count = populate_stops(user_id)
        print()
        paths_count = populate_paths(user_id)
        print()
        routes_count = populate_routes(user_id)
        print()
        vehicles_count = populate_vehicles(user_id)
        print()
        drivers_count = populate_drivers(user_id)
        print()
        trips_count = populate_daily_trips(user_id)
        print()
        deployments_count = populate_deployments(user_id)
        
        print()
        print("=" * 60)
        print("[SUCCESS] Database initialization completed successfully!")
        print("=" * 60)
        print()
        print(f"Summary:")
        print(f"  - Stops: {stops_count}")
        print(f"  - Paths: {paths_count}")
        print(f"  - Routes: {routes_count}")
        print(f"  - Vehicles: {vehicles_count}")
        print(f"  - Drivers: {drivers_count}")
        print(f"  - Trips: {trips_count}")
        print(f"  - Deployments: {deployments_count}")
        print()
        print("Note: All records include audit columns (created_by, updated_by)")
        print("      and support soft delete (deleted_at, deleted_by)")
        print("      All data is Bengaluru-specific and unique")
        
    except Exception as e:
        print(f"\n[ERROR] Error during database population: {e}")
        raise


if __name__ == "__main__":
    main()
