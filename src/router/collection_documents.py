import base64
import binascii
import urllib
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status, logger
from fastapi.responses import Response

from src.Model.CollectionDocument import CollectionDocument, CreateCollectionDocument, CreateCollectionDocumentDB, \
    CollectionDocumentMetadata

import src.SQL as SQL
from src.SQL.Enum.Privilege import ADMIN_USER

from src.Service import Auth
from src.repository import collection_documents_repository
from src.Service.Collection.collection_validator import check_if_user_can_view_collection

collection_documents_router = APIRouter()


@collection_documents_router.post(path="/", status_code=status.HTTP_201_CREATED,
                                  response_model=CollectionDocumentMetadata)
async def create_collection_document(
        user: Annotated[Auth.AuthorizedUser, Depends(Auth.authorized_user())],
        sql_session: Annotated[SQL.AsyncSession, Depends(SQL.get_async_session)],
        collection_document: CreateCollectionDocument,
):
    if not await check_if_user_can_view_collection(sql_session, collection_document.collection_id,
                                                   user.user_id) and user.user_privilege != ADMIN_USER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    try:
        try:
            file_data = base64.b64decode(collection_document.file_data)
        except Exception:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Invalid file_data")

        document_data = CreateCollectionDocumentDB(
            collection_id=collection_document.collection_id,
            document_name=collection_document.document_name,
            file_type=collection_document.file_type,
            file_data=file_data
        )

        result = await collection_documents_repository.create(sql_session, document_data)

        return CollectionDocumentMetadata(
            document_id=result.document_id,
            collection_id=result.collection_id,
            document_name=result.document_name,
            file_type=result.file_type
        )
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@collection_documents_router.put(path="/", status_code=status.HTTP_200_OK, response_model=CollectionDocumentMetadata)
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

        return CollectionDocumentMetadata(
            document_id=document.document_id,
            collection_id=document.collection_id,
            document_name=document.document_name,
            file_type=document.file_type
        )
    except HTTPException as error:
        raise error
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@collection_documents_router.delete(path="/{document_id}", status_code=status.HTTP_200_OK,
                                    response_model=CollectionDocumentMetadata)
async def delete_collection_document(
        user: Annotated[Auth.AuthorizedUser, Depends(Auth.authorized_user())],
        sql_session: Annotated[SQL.AsyncSession, Depends(SQL.get_async_session)],
        document_id: int,
):
    try:
        deleted_document = await collection_documents_repository.delete(sql_session, document_id, user)

        return CollectionDocumentMetadata(
            document_id=deleted_document.document_id,
            collection_id=deleted_document.collection_id,
            document_name=deleted_document.document_name,
            file_type=deleted_document.file_type
        )
    except HTTPException as error:
        raise error
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@collection_documents_router.get(path="/{document_id}", status_code=status.HTTP_200_OK,
                                 response_model=CollectionDocumentMetadata)
async def get_document_by_id(
        user: Annotated[Auth.AuthorizedUser, Depends(Auth.authorized_user())],
        sql_session: Annotated[SQL.AsyncSession, Depends(SQL.get_async_session)],
        document_id: int,
):
    try:
        document = await collection_documents_repository.get_by_id(sql_session, document_id)

        if not document:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

        if not await check_if_user_can_view_collection(sql_session, document.collection_id,
                                                       user.user_id) and user.user_privilege != ADMIN_USER:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

        return CollectionDocumentMetadata(
            document_id=document.document_id,
            collection_id=document.collection_id,
            document_name=document.document_name,
            file_type=document.file_type
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@collection_documents_router.get(path="/collection/{collection_id}", status_code=status.HTTP_200_OK,
                                 response_model=List[CollectionDocumentMetadata])
async def get_collection_documents(
        user: Annotated[Auth.AuthorizedUser, Depends(Auth.authorized_user())],
        sql_session: Annotated[SQL.AsyncSession, Depends(SQL.get_async_session)],
        collection_id: int,
):
    if not await check_if_user_can_view_collection(sql_session, collection_id,
                                                   user.user_id) and user.user_privilege != ADMIN_USER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    try:
        documents = await collection_documents_repository.get(sql_session, collection_id)

        if len(documents) == 0:
            raise HTTPException(status_code=status.HTTP_204_NO_CONTENT)

        return documents
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Nowy endpoint do pobierania zawartości pliku
@collection_documents_router.get(path="/{document_id}/content", status_code=status.HTTP_200_OK)
async def get_document_content(
        user: Annotated[Auth.AuthorizedUser, Depends(Auth.authorized_user())],
        sql_session: Annotated[SQL.AsyncSession, Depends(SQL.get_async_session)],
        document_id: int,
):
    """
        Returns content of the file in binary format.

        It returns the file in naive format such as PDF, JPEG, PNG, etc.
        Content-type is automatically assigned depending on the file type.
    """
    try:
        document = await collection_documents_repository.get_by_id(sql_session, document_id)

        if not document:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

        if not await check_if_user_can_view_collection(sql_session, document.collection_id,
                                                       user.user_id) and user.user_privilege != ADMIN_USER:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

        mime_types = {
            "pdf": "application/pdf",
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "png": "image/png",
            "gif": "image/gif",
            "doc": "application/msword",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "xls": "application/vnd.ms-excel",
            "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        }

        media_type = mime_types.get(document.file_type.lower(), "application/octet-stream")
        encoded_filename = urllib.parse.quote(f"{document.document_name}.{document.file_type}")

        return Response(
            content=document.file_data,
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="{encoded_filename}"',
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
            }
        )
    except Exception as e:
        logger.logger.error(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))