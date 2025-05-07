from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from typing import Annotated, List
import src.Service.Auth as Auth
import src.repository.chat_repository as chat_repository
from src.Model.Chat import Message, Conversation, CreateConversation, SendMessage, MarkMessagesReadRequest
import json
from datetime import datetime
from fastapi import logger

chat_router = APIRouter()

active_connections = {}


@chat_router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await websocket.accept()
    active_connections[user_id] = websocket
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)

            # Validate user is authorized to send to this conversation
            # (You would add authentication logic here)

            # Save message to MongoDB
            message = Message(
                conversation_id=message_data["conversation_id"],
                sender_id=user_id,
                content=message_data["content"],
                message_type=message_data.get("message_type", "text"),
                file_url=message_data.get("file_url"),
                created_at=datetime.utcnow(),
                read_by=[user_id],
            )
            message_id = await chat_repository.save_message(message)
            message.id = message_id

            # Get conversation to find recipients
            conversation = await chat_repository.get_conversation(
                message.conversation_id
            )
            if conversation:
                # Send to all active participants
                for participant_id in conversation.participants:
                    if (
                        participant_id != user_id
                        and participant_id in active_connections
                    ):
                        await active_connections[participant_id].send_text(
                            message.model_dump_json()
                        )
    except WebSocketDisconnect:
        if user_id in active_connections:
            del active_connections[user_id]
    except Exception as e:
        logger.logger.error(f"WebSocket error: {str(e)}")
        if user_id in active_connections:
            del active_connections[user_id]


@chat_router.post("/conversations", response_model=Conversation)
async def create_conversation(
    user: Annotated[Auth.AuthorizedUser, Depends(Auth.authorized_user())],
    request: CreateConversation,
):
    try:
        # Validate that the user is part of the conversation
        if user.user_id not in request.participants:
            request.participants.append(user.user_id)

        conversation = Conversation(
            participants=request.participants,
            title=request.title,
            created_at=datetime.utcnow(),
        )

        conversation_id = await chat_repository.create_conversation(conversation)
        conversation.id = conversation_id
        return conversation
    except Exception as e:
        logger.logger.error(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create conversation",
        )


@chat_router.get("/conversations", response_model=List[Conversation])
async def get_user_conversations(
    user: Annotated[Auth.AuthorizedUser, Depends(Auth.authorized_user())]
):
    try:
        return await chat_repository.get_user_conversations(user.user_id)
    except Exception as e:
        logger.logger.error(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve conversations",
        )


@chat_router.get(
    "/conversations/{conversation_id}/messages", response_model=List[Message]
)
async def get_conversation_messages(
    user: Annotated[Auth.AuthorizedUser, Depends(Auth.authorized_user())],
    conversation_id: str,
    limit: int = 50,
    skip: int = 0,
):
    try:
        # Validate user is part of conversation
        conversation = await chat_repository.get_conversation(conversation_id)
        if not conversation or user.user_id not in conversation.participants:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User not authorized to access this conversation",
            )

        messages = await chat_repository.get_conversation_messages(
            conversation_id, limit, skip
        )

        # Mark messages as read
        await chat_repository.mark_messages_as_read(conversation_id, user.user_id)

        return messages
    except HTTPException:
        raise
    except Exception as e:
        logger.logger.error(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve messages",
        )


@chat_router.post("/messages/read")
async def mark_messages_read(
        user: Annotated[Auth.AuthorizedUser, Depends(Auth.authorized_user())],
        request: MarkMessagesReadRequest,
):
    try:
        # Verify user has access to all the messages
        authorized_message_ids = []

        for message_id in request.message_ids:
            message = await chat_repository.get_message_by_id(message_id)
            if not message:
                continue

            conversation = await chat_repository.get_conversation(message.conversation_id)
            if conversation and user.user_id in conversation.participants:
                authorized_message_ids.append(message_id)

        # Mark only authorized messages as read
        modified_count = 0
        if authorized_message_ids:
            modified_count = await chat_repository.mark_specific_messages_as_read(
                authorized_message_ids, user.user_id
            )

        return {"marked_count": modified_count}
    except Exception as e:
        logger.logger.error(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark messages as read"
        )
