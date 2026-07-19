# Config: environment variables and application settings
# Owner: AI2 - Trung
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from same directory as this file
load_dotenv(dotenv_path=Path(__file__).parent / ".env")

OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "dummy_key")
OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_MODEL_NAME: str = os.getenv("OPENAI_MODEL_NAME", "gpt-3.5-turbo")

REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
OLLAMA_URL: str = os.getenv("OLLAMA_URL", "http://localhost:11434")
JWT_SECRET: str = os.getenv("JWT_SECRET", "")
LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "ollama")  # "mock" | "openai" | "ollama" | "hf_inference"
HF_TOKEN: str = os.getenv("HF_TOKEN", "")
KNOWLEDGE_BASE_PATH: str = str(
    Path(__file__).parent / ".." / "knowledge-base" / "knowledge_base.json"
)
