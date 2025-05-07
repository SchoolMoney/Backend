import motor.motor_asyncio
from src.config import MONGODB_URL, MONGODB_DB_NAME

client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URL)
db = client[MONGODB_DB_NAME]

# Collections
messages_collection = db.messages
conversations_collection = db.conversations
