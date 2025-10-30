from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    app_env: str = Field(default="development")
    secret_key: str = Field(default="change_me")

    database_url: str = Field(default="postgresql+psycopg2://postgres:postgres@db:5432/def_civil")
    redis_url: str = Field(default="redis://redis:6379/0")

    waha_base_url: str = Field(default="http://waha:3000")
    waha_api_key: str = Field(default="changeme")

    gemini_api_key: str = Field(default="")
    groq_api_key: str = Field(default="")
    ollama_base_url: str = Field(default="http://ollama:11434")

    allowed_jurisdictions: str = Field(default="San Rafael,Mendoza")

    class Config:
        env_file = ".env"
        env_prefix = ""
        case_sensitive = False

settings = Settings()