import os
from typing import List
from dotenv import load_dotenv

# Load environment variables from root .env file if present
backend_dir = os.path.abspath(os.path.dirname(__file__))
root_dir = os.path.abspath(os.path.join(backend_dir, ".."))
env_path = os.path.join(root_dir, ".env")
if os.path.isfile(env_path):
    load_dotenv(env_path)

class Settings:
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "dummy_key_replace_with_real")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "campusmind_super_secret_jwt_key_2026")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))

    EMBEDDING_PROVIDER: str = os.getenv("EMBEDDING_PROVIDER", "sentence-transformers")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

    raw_chroma = os.getenv("CHROMA_DB_DIR", "./backend/chroma_db")
    if not os.path.isabs(raw_chroma):
        CHROMA_DB_DIR: str = os.path.abspath(os.path.join(root_dir, raw_chroma.lstrip("./")))
    else:
        CHROMA_DB_DIR: str = raw_chroma

    raw_db_url = os.getenv("DATABASE_URL", "sqlite:///./backend/campusmind.db")
    if raw_db_url.startswith("sqlite:///"):
        db_path = raw_db_url.replace("sqlite:///", "")
        if not os.path.isabs(db_path):
            abs_db_path = os.path.abspath(os.path.join(root_dir, db_path.lstrip("./")))
            DATABASE_URL: str = f"sqlite:///{abs_db_path}"
        else:
            DATABASE_URL: str = raw_db_url
    else:
        DATABASE_URL: str = raw_db_url

    RETRIEVAL_TOP_K: int = int(os.getenv("RETRIEVAL_TOP_K", "5"))
    SIMILARITY_THRESHOLD: float = float(os.getenv("SIMILARITY_THRESHOLD", "0.25"))
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000", "*"]

settings = Settings()


