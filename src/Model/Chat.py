from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional
from enum import Enum


class MessageType(str, Enum):
    TEXT = "text"
    FILE = "file"


class Message(BaseModel):
    id: Optional[str] = None
    conversation_id: str
    sender_id: int
    content: str
    message_type: MessageType = MessageType.TEXT
    file_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    read_by: List[int] = []


class Conversation(BaseModel):
    id: Optional[str] = None
    participants: List[int]
    title: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_message_at: Optional[datetime] = None


class CreateConversation(BaseModel):
    participants: List[int]
    title: Optional[str] = None


class SendMessage(BaseModel):
    content: str
    message_type: MessageType = MessageType.TEXT
    file_url: Optional[str] = None
