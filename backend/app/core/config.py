from dotenv import load_dotenv
import os


load_dotenv()


# ==========================================
# Authentication
# ==========================================

SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "dev-secret-key-change-this"
)

ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = 30


# ==========================================
# LLM Configuration
# ==========================================

LLM_API_KEY = os.getenv(
    "LLM_API_KEY"
)

LLM_MODEL = os.getenv(
    "LLM_MODEL",
    "openai/gpt-oss-20b"
)

LLM_BASE_URL = os.getenv(
    "LLM_BASE_URL",
    "https://api.groq.com/openai/v1"
)


# ==========================================
# RAG Configuration
# ==========================================

RAG_DISTANCE_THRESHOLD = float(
    os.getenv(
        "RAG_DISTANCE_THRESHOLD",
        "0.7"
    )
)