# Config: environment variables and application settings
# Owner: AI2 - Trung
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from same directory as this file
load_dotenv(dotenv_path=Path(__file__).parent / ".env")

OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
OLLAMA_URL: str = os.getenv("OLLAMA_URL", "http://localhost:11434")
JWT_SECRET: str = os.getenv("JWT_SECRET", "")
LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai")  # "openai" | "ollama"
KNOWLEDGE_BASE_PATH: str = str(
    Path(__file__).parent / ".." / "knowledge-base" / "knowledge_base.json"
)
