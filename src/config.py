import os
from dotenv import load_dotenv

APP_TITLE = "SchoolMoney Backend"
APP_DESCRIPTION = "SchoolMoney REST API"

load_dotenv()

API_PORT = os.getenv("PORT", 8000)
API_ADDRESS = os.getenv("ADDRESS", "0.0.0.0")

DB_ADDRESS = os.getenv("DB_ADDRESS", "localhost")
DB_PORT = os.getenv("DB_PORT", 5432)
DB_NAME = os.getenv("DB_NAME", "postgres")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_DROP_EXISTING_TABLES = os.getenv("DB_DROP_EXISTING_TABLES", False)
