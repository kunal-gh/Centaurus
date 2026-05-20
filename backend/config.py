"""
Configuration management.
Loads environment variables and exposes typed settings.
Spec Reference: Section 6.1
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    MOCK_MODE: str = os.getenv("BOOKLEAF_MOCK_MODE", "")

    @property
    def is_mock_mode(self) -> bool:
        """
        Mock mode is enabled when:
        - BOOKLEAF_MOCK_MODE is truthy, OR
        - OPENAI_API_KEY is missing or explicitly set to "test"
        This keeps the demo runnable without external keys.
        """
        if self.MOCK_MODE.strip().lower() in {"1", "true", "yes", "on"}:
            return True
        return (self.OPENAI_API_KEY or "").strip().lower() in {"", "test"}

    @classmethod
    def validate(cls) -> None:
        """
        Validates that all required environment variables are set.
        Raises ValueError with a list of missing variables.
        """
        # In mock mode we intentionally allow missing external keys.
        if settings.is_mock_mode:
            return

        missing = []
        if not cls.SUPABASE_URL:
            missing.append("SUPABASE_URL")
        if not cls.SUPABASE_KEY:
            missing.append("SUPABASE_KEY")
        if not cls.OPENAI_API_KEY:
            missing.append("OPENAI_API_KEY")
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")


settings = Settings()
