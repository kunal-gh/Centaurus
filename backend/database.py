"""
Supabase client singleton.
Ensures only one client instance is created per application lifecycle.
Spec Reference: Section 6.2
"""
from supabase import create_client, Client
from backend.config import settings
from backend.mock_data import load_mock_tables
from backend.mock_supabase import MockSupabaseClient

_client = None


def get_supabase() -> Client:
    """
    Returns the Supabase client, creating it on first call.
    Validates environment variables before creating client.
    """
    global _client
    if _client is None:
        # In mock mode, we return an in-memory Supabase-like client.
        if settings.is_mock_mode or not (settings.SUPABASE_URL and settings.SUPABASE_KEY):
            _client = MockSupabaseClient(load_mock_tables())
            return _client

        settings.validate()
        _client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    return _client
