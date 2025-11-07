from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    app_env: str = Field(default="development")
    secret_key: str = Field(default="change_me")

    database_url: str = Field(default="postgresql+psycopg2://postgres:postgres@db:5432/defensoria_civil?options=-c client_encoding=LATIN1")
    redis_url: str = Field(default="redis://redis:6379/0")

    waha_base_url: str = Field(default="http://waha:3000")
    waha_api_key: str = Field(default="changeme")

    # Ollama Cloud (proveedor primario)
    ollama_cloud_api_key: str = Field(default="")
    ollama_cloud_base_url: str = Field(default="https://ollama.com")
    
    # Ollama Local (fallback)
    ollama_base_url: str = Field(default="http://localhost:11434")
    
    # Gemini (fallback crítico)
    gemini_api_key: str = Field(default="")
    groq_api_key: str = Field(default="")  # Legacy, puede removerse
    
    # Configuración de modelos por tarea
    llm_chat_model: str = Field(default="minimax-m2:cloud")
    llm_reasoning_model: str = Field(default="deepseek-v3.1:671b-cloud")
    llm_vision_model: str = Field(default="qwen3-vl:235b-cloud")
    llm_hallucination_model: str = Field(default="glm-4.6:cloud")
    llm_embedding_model: str = Field(default="nomic-embed-text:latest")

    allowed_jurisdictions: str = Field(default="San Rafael,Mendoza")

    class Config:
        # Buscar .env en la raíz del proyecto (dos niveles arriba desde core/)
        import os
        from pathlib import Path
        
        # backend/src/core/config.py -> subir a backend/src -> backend -> raíz
        project_root = Path(__file__).parent.parent.parent.parent
        
        # Priorizar .env.local si existe (para desarrollo local sin Docker)
        env_file_local = project_root / ".env.local"
        env_file_default = project_root / ".env"
        env_file = env_file_local if env_file_local.exists() else env_file_default
        
        # En algunos entornos Windows los .env pueden guardarse en CP1252; usar latin-1 evita errores de decodificación
        env_file_encoding = "latin-1"

        env_prefix = ""
        case_sensitive = False
        extra = "ignore"  # Ignorar variables extra del .env

settings = Settings()
