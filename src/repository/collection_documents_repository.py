from http.client import HTTPException
from typing import Sequence, Optional

from fastapi import logger, status, HTTPException

from src.Model.CollectionDocument import CreateCollectionDocument, CollectionDocument
from src.SQL import AsyncSession, select
from src.SQL.Enum.Privilege import ADMIN_USER
from src.SQL.Tables.Collection import CollectionDocuments
from src.Service.Auth import AuthorizedUser
from src.Service.Collection.collection_validator import check_if_user_can_view_collection


async def create(session: AsyncSession, collection_doc:CreateCollectionDocument) -> CollectionDocument:
    collection_document = CollectionDocuments(**collection_doc.model_dump())
    try:
        session.add(collection_document)
        await session.commit()
    except Exception as error:
        logger.logger.error(error)
        raise error
    return collection_document



async def update(session: AsyncSession, collection_document:CollectionDocument) -> Optional[CollectionDocument]:
    try:
        document = await get_by_id(session, collection_document.document_id)
        if document is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

        update_data = collection_document.model_dump(exclude_unset=True)
        for key,value in update_data.items():
            setattr(document, key, getattr(collection_document, key))

        session.add(document)
        await session.commit()
        await session.refresh(document)
    except Exception as error:
        logger.logger.error(error)
        raise error
    return document



async def get(session: AsyncSession, collection_id: int) -> Sequence[CollectionDocument]:
    query = select(CollectionDocuments).filter(CollectionDocuments.collection_id == collection_id)

    try:
        list_of_documents = (await session.exec(query)).all()
    except Exception as error:
        logger.logger.error(error)
        raise error
    return list_of_documents

async def get_by_id(session: AsyncSession, collection_document_id: int) -> Optional[CollectionDocument]:
    query = select(CollectionDocuments).filter(CollectionDocuments.document_id == collection_document_id)

    try:
        document = (await session.exec(query)).first()
    except Exception as error:
        logger.logger.error(error)
        raise error

    return document if document else None

async def delete(session: AsyncSession, collection_document_id: int, user: AuthorizedUser) -> Optional[CollectionDocument]:
    try:
        document = await get_by_id(session, collection_document_id)
        if document is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

        if not await check_if_user_can_view_collection(session, document.collection_id,
                                                       user.user_id) and user.user_privilege != ADMIN_USER:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

        await session.delete(document)
        await session.commit()
        return document
    except Exception as error:
        await session.rollback()
        logger.logger.error(error)
        raise error
