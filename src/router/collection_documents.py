from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status

from src.Model.CollectionDocument import CollectionDocument, CreateCollectionDocument

import src.SQL as SQL
from src.SQL.Enum.Privilege import ADMIN_USER

from src.Service import Auth
from src.repository import collection_documents_repository
from src.repository.collection_repository import check_if_user_can_view_collection

collection_documents_router = APIRouter()



@collection_documents_router.post(path="/", status_code=status.HTTP_201_CREATED, response_model=CollectionDocument)
async def create_collection_document(
        user: Annotated[Auth.AuthorizedUser, Depends(Auth.authorized_user())],
        sql_session: Annotated[SQL.AsyncSession, Depends(SQL.get_async_session)],
        collection_document: CreateCollectionDocument,
):
    if not await check_if_user_can_view_collection(sql_session, collection_document.collection_id,
                                                   user.user_id) and user.user_privilege != ADMIN_USER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    try:
        result = await collection_documents_repository.create(sql_session, collection_document)
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))

    return result

@collection_documents_router.put(path="/", status_code=status.HTTP_200_OK, response_model=CollectionDocument)
async def update_collection_document(
        user: Annotated[Auth.AuthorizedUser, Depends(Auth.authorized_user())],
        sql_session: Annotated[SQL.AsyncSession, Depends(SQL.get_async_session)],
        collection_document: CollectionDocument,
):
    if not await check_if_user_can_view_collection(sql_session, collection_document.collection_id,
                                                   user.user_id) and user.user_privilege != ADMIN_USER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    try:
        document = await collection_documents_repository.update(sql_session, collection_document)
    except HTTPException as error:
        raise error
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))

    return document

@collection_documents_router.delete(path="/{document_id}", status_code=status.HTTP_200_OK, response_model=CollectionDocument)
async def delete_collection_document(
        user: Annotated[Auth.AuthorizedUser, Depends(Auth.authorized_user())],
        sql_session: Annotated[SQL.AsyncSession, Depends(SQL.get_async_session)],
        collection_document_id: int,
):
    try:
        deleted_document = await collection_documents_repository.delete(sql_session, collection_document_id, user)
    except HTTPException as error:
        raise error
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))

    return deleted_document


@collection_documents_router.get(path="/{document_id}", status_code=status.HTTP_200_OK,
                                 response_model=CollectionDocument)
async def get_document_by_id(
        user: Annotated[Auth.AuthorizedUser, Depends(Auth.authorized_user())],
        sql_session: Annotated[SQL.AsyncSession, Depends(SQL.get_async_session)],
        document_id: int,
):
    try:
        document = await collection_documents_repository.get_by_id(sql_session, document_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    if not await check_if_user_can_view_collection(sql_session, document.collection_id, user.user_id) and user.user_privilege != ADMIN_USER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    return document

@collection_documents_router.get(path="/collection/{collection_id}", status_code=status.HTTP_200_OK,
                                 response_model=List[CollectionDocument])
async def get_collection_documents(
        user: Annotated[Auth.AuthorizedUser, Depends(Auth.authorized_user())],
        sql_session: Annotated[SQL.AsyncSession, Depends(SQL.get_async_session)],
        collection_id: int,
):
    if not await check_if_user_can_view_collection(sql_session, collection_id, user.user_id) and user.user_privilege != ADMIN_USER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    try:
        documents = await collection_documents_repository.get(sql_session, collection_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    if len(documents) == 0:
        raise HTTPException(status_code=status.HTTP_204_NO_CONTENT)
    return documents

