from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Bus Kar! - Transit AI Agent API & MCP Plugin"
    environment: str = "development"
    debug: bool = True
    port: int = 8000
    host: str = "0.0.0.0"

    database_url: str = "sqlite+aiosqlite:///./transit.db"
    
    # Delhi OTD
    delhi_otd_api_key: str = "mock_key"
    delhi_otd_base_url: str = "https://otd.delhi.gov.in/api/realtime"
    
    redis_url: str = "redis://localhost:6379/0"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
