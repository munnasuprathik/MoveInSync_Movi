"""
Database client for Movi transport management system.

Provides a singleton Supabase client instance for database operations.
"""

import os
from typing import Optional
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL: Optional[str] = os.getenv("SUPABASE_URL")
SUPABASE_KEY: Optional[str] = os.getenv("SUPABASE_KEY")

# Global client instance
_client: Optional[Client] = None


def get_client() -> Client:
    """
    Get or create Supabase client instance (singleton pattern).
    
    Returns:
        Client: Supabase client instance
        
    Raises:
        ValueError: If SUPABASE_URL or SUPABASE_KEY are not set in environment
    """
    global _client
    
    if _client is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError(
                "Please set SUPABASE_URL and SUPABASE_KEY in your .env file"
            )
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    return _client


def reset_client() -> None:
    """
    Reset the client instance (useful for testing or reconnection).
    """
    global _client
    _client = None

