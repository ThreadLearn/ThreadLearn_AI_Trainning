# Config: environment variables and application settings
# Owner: AI2 - Trung
import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
JWT_SECRET = os.getenv("JWT_SECRET", "")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")  # "openai" | "ollama"
KNOWLEDGE_BASE_PATH = os.path.join(
    os.path.dirname(__file__), "..", "knowledge-base", "knowledge_base.json"
)
