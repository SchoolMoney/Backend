import os
from dotenv import load_dotenv

APP_TITLE = "SchoolMoney Backend"
APP_DESCRIPTION = "SchoolMoney REST API"
API_PREFIX = "/api"


load_dotenv()

API_PORT = os.getenv("PORT", 8000)
API_ADDRESS = os.getenv("ADDRESS", "0.0.0.0")
CORS_FRONTEND = os.getenv("CORS_FRONTEND", "http://localhost:5173")

DB_ADDRESS = os.getenv("DB_ADDRESS", "localhost")
DB_PORT = os.getenv("DB_PORT", 5432)
DB_NAME = os.getenv("DB_NAME", "postgres")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_DROP_EXISTING_TABLES = os.getenv("DB_DROP_EXISTING_TABLES", "FALSE")

SECRET_KEY = os.getenv(
    "SECRET_KEY", "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
)

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", 6379)
REDIS_DB = os.getenv("REDIS_DB", 0)

JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRATION_PERIOD = 3600
REFRESH_TOKEN_EXPIRATION_PERIOD = 3600 * 2

PASSWORD_HASH_SALT = os.getenv("PASSWORD_HASH_SALT", "$2b$12$tEwk7HxlN0EMUr4jx1dJtu")

DEFAULT_ADMIN_USERNAME = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
DEFAULT_ADMIN_PASSWORD = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin")

MONGODB_HOST = os.getenv("MONGODB_HOST", "localhost")
MONGODB_PORT = os.getenv("MONGODB_PORT", 27017)
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "chat_db")
MONGODB_URL = f"mongodb://{MONGODB_HOST}:{MONGODB_PORT}"
