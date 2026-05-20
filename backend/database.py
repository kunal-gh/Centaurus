"""
Supabase client singleton.
Ensures only one client instance is created per application lifecycle.
Spec Reference: Section 6.2
"""
from supabase import create_client, Client
from backend.config import settings

_client = None


def get_supabase() -> Client:
    """
    Returns the Supabase client, creating it on first call.
    Validates environment variables before creating client.
    """
    global _client
    if _client is None:
        settings.validate()
        _client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    return _client
