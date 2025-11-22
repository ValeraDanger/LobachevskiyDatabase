import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

DB_NAME = os.getenv("DB_NAME", "postgres")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_MIN_POOL_SIZE = int(os.getenv("DB_MIN_POOL_SIZE", "10"))
DB_MAX_POOL_SIZE = int(os.getenv("DB_MAX_POOL_SIZE", "100"))

TIMEZONE_OFFSET = int(os.getenv("TIMEZONE_OFFSET", "3"))

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "CHANGE_ME_IN_PROD")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRES_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRES_MINUTES", "30"))
REFRESH_TOKEN_EXPIRES_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRES_DAYS", "7"))
DEFAULT_ROLE = os.getenv("DEFAULT_ROLE", "viewer")

DOC_STORAGE_DIR = Path(os.getenv("DOC_STORAGE_DIR", "/app/storage/documents")).resolve()
RAG_API_URL = os.getenv("RAG_API_URL", "http://rag-api:8080")