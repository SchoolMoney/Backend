from bson import ObjectId
from src.NoSQL.connection import messages_collection, conversations_collection
from src.Model.Chat import Message, Conversation
from typing import List, Optional


async def create_conversation(conversation: Conversation) -> str:
    result = await conversations_collection.insert_one(
        conversation.model_dump(exclude={"id"})
    )
    return str(result.inserted_id)


async def get_conversation(conversation_id: str) -> Optional[Conversation]:
    result = await conversations_collection.find_one({"_id": ObjectId(conversation_id)})
    if result:
        result["id"] = str(result.pop("_id"))
        return Conversation(**result)
    return None


async def get_user_conversations(user_id: int) -> List[Conversation]:
    cursor = conversations_collection.find({"participants": user_id})
    conversations = []
    async for doc in cursor:
        doc["id"] = str(doc.pop("_id"))
        conversations.append(Conversation(**doc))
    return conversations


async def save_message(message: Message) -> str:
    result = await messages_collection.insert_one(message.model_dump(exclude={"id"}))
    await conversations_collection.update_one(
        {"_id": ObjectId(message.conversation_id)},
        {"$set": {"last_message_at": message.created_at}},
    )
    return str(result.inserted_id)


async def get_conversation_messages(
    conversation_id: str, limit: int = 50, skip: int = 0
) -> List[Message]:
    cursor = (
        messages_collection.find({"conversation_id": conversation_id})
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )
    messages = []
    async for doc in cursor:
        doc["id"] = str(doc.pop("_id"))
        messages.append(Message(**doc))
    return messages[::-1]  # Reverse to get chronological order


async def mark_messages_as_read(conversation_id: str, user_id: int) -> int:
    result = await messages_collection.update_many(
        {"conversation_id": conversation_id, "read_by": {"$ne": user_id}},
        {"$push": {"read_by": user_id}},
    )
    return result.modified_count

async def mark_specific_messages_as_read(message_ids: List[str], user_id: int) -> int:
    """Mark specific messages as read by a user"""
    object_ids = [ObjectId(msg_id) for msg_id in message_ids]
    result = await messages_collection.update_many(
        {"_id": {"$in": object_ids}, "read_by": {"$ne": user_id}},
        {"$push": {"read_by": user_id}}
    )
    return result.modified_count


async def get_message_by_id(message_id: str) -> Optional[Message]:
    """Get a message by its ID"""
    result = await messages_collection.find_one({"_id": ObjectId(message_id)})
    if result:
        result["id"] = str(result.pop("_id"))
        return Message(**result)
    return None
