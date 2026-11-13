import os
from typing import List
from dotenv import load_dotenv
from pydantic import BaseModel

# Load backend/.env (if present) before reading any settings.
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"))

class Settings(BaseModel):
    APP_NAME: str = "AI Coding Mentor API"
    APP_ENV: str = os.getenv("APP_ENV", "development")
    APP_SECRET_KEY: str = os.getenv("APP_SECRET_KEY", "dbce-mentor-super-secret-key-2026-production")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000"
    ]
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    
    # Code Execution (Judge0)
    JUDGE0_API_URL: str = os.getenv("JUDGE0_API_URL", "")
    JUDGE0_API_KEY: str = os.getenv("JUDGE0_API_KEY", "")
    
    # AI Integration
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "ollama")  # ollama, gemini, openai, groq, simulated
    AI_API_KEY: str = os.getenv("AI_API_KEY", "")
    AI_MODEL: str = os.getenv("AI_MODEL", "gemma3:latest")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "gemma3:latest")

settings = Settings()
