import os
import tempfile
from pydantic_settings import BaseSettings, SettingsConfigDict

def get_default_database_url() -> str:
    # On Vercel, AWS Lambda, or containerized serverless, root directory is read-only
    # The only writable directory is /tmp
    if os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
        return "sqlite+aiosqlite:////tmp/transit.db"
    return "sqlite+aiosqlite:///./transit.db"

class Settings(BaseSettings):
    app_name: str = "Bus Kar! - Transit AI Agent API & MCP Plugin"
    environment: str = "development"
    debug: bool = False
    port: int = 8000
    host: str = "0.0.0.0"

    database_url: str = get_default_database_url()
    
    # Delhi OTD
    delhi_otd_api_key: str = "mock_key"
    delhi_otd_base_url: str = "https://otd.delhi.gov.in/api/realtime"
    
    redis_url: str = "redis://localhost:6379/0"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
