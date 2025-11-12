# Database Module

Well-organized database layer for Movi transport management system.

## Structure

```
database/
├── __init__.py          # Module exports
├── client.py            # Database client (Supabase connection)
├── repositories.py      # Repository pattern for data access
├── utils.py             # Utility functions (soft delete, queries)
├── schema.sql           # Database schema definition
└── init_database.py     # Database initialization script
```

## Usage

### Basic Connection

```python
from database import get_client

client = get_client()
stops = client.table("stops").select("*").execute()
```

### Using Repositories

```python
from database import StopsRepository

stops_repo = StopsRepository()
all_stops = stops_repo.get_all_active()
stop = stops_repo.get_by_id(1)
```

### Using Utilities

```python
from database import get_active_stops, soft_delete_stop

# Get all active stops
stops = get_active_stops()

# Soft delete a stop
soft_delete_stop(stop_id=1, deleted_by=user_id)
```

## Architecture

- **Repository Pattern**: Clean separation of data access logic
- **Singleton Client**: Single database connection instance
- **Type Hints**: Full type annotations for better IDE support
- **Soft Delete**: Built-in support for soft delete operations
- **Active Records**: Automatic filtering of deleted records

## Files

- `client.py`: Database connection management
- `repositories.py`: Data access layer with repository pattern
- `utils.py`: Helper functions for common operations
- `schema.sql`: Complete database schema
- `init_database.py`: Sample data population script

