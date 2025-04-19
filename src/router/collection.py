from datetime import date
from typing import Annotated, List, Optional, Sequence
from fastapi import APIRouter, Depends, HTTPException, Query, status, logger

from src.Model.CollectionModel import CreateCollection, CollectionOperationList
import src.SQL as SQL
from src.Model.CollectionStatusEnum import CollectionStatusEnum
from src.SQL.Enum.Privilege import ADMIN_USER
from src.SQL.Tables import Collection, Parent
from src.Service import Auth
from src.Service.Collection import collection_service
from src.repository import collection_repository
from src.repository.collection_repository import get_collection_operations_list_in_collection

collection_router = APIRouter()


@collection_router.get("", status_code=status.HTTP_200_OK, response_model=List[Collection])
async def get(
    user: Annotated[Auth.AuthorizedUser, Depends(Auth.authorized_user())],
    sql_session: Annotated[SQL.AsyncSession, Depends(SQL.get_async_session)],
    name: Optional[str] = Query(None),
    start_date_from: Optional[date] = Query(None),
    start_date_to: Optional[date] = Query(None),
    end_date_from: Optional[date] = Query(None),
    end_date_to: Optional[date] = Query(None),
    collection_status: Optional[CollectionStatusEnum] = Query(None),
) -> Sequence[Collection]:
    try:
        return await collection_repository.get(
            sql_session, user.user_privilege, user.user_id, name, start_date_from, start_date_to, end_date_from, end_date_to, collection_status
        )
    except ValueError as e:
        logger.logger.error(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
    except Exception as e:
        logger.logger.error(f"Error retrieving collections: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve collections"
        )


@collection_router.get("/{collection_id}", status_code=status.HTTP_200_OK, response_model=Collection)
async def get_by_id(
    user: Annotated[Auth.AuthorizedUser, Depends(Auth.authorized_user())],
    collection_id: int,
    sql_session: Annotated[SQL.AsyncSession, Depends(SQL.get_async_session)],
) -> Collection:
    try:
        return await collection_repository.get_by_id(sql_session, collection_id)
    except Exception as e:
        logger.logger.error(f"Error retrieving collection by ID {collection_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve collection"
        )


@collection_router.post("", response_model=Collection, status_code=status.HTTP_201_CREATED)
async def create(
    user: Annotated[Auth.AuthorizedUser, Depends(Auth.authorized_user())],
    collection: CreateCollection,
    sql_session: Annotated[SQL.AsyncSession, Depends(SQL.get_async_session)],
) -> Collection:
    try:
        parent_id = (await sql_session.exec(SQL.select(Parent.id).where(Parent.account_id == user.user_id))).first()
        print(parent_id)
        return await collection_service.create(sql_session, parent_id, collection)
    except Exception as e:
        logger.logger.error(f"Error creating collection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create collection"
        )


@collection_router.put("/{collection_id}", status_code=status.HTTP_200_OK, response_model=Collection)
async def update(
    user: Annotated[Auth.AuthorizedUser, Depends(Auth.authorized_user(ADMIN_USER))],
    collection_id: int,
    updated_collection: Collection,
    sql_session: Annotated[SQL.AsyncSession, Depends(SQL.get_async_session)],
) -> Collection:
    try:
        return await collection_service.update(
            sql_session, collection_id, updated_collection
        )
    except Exception as e:
        logger.logger.error(f"Error updating collection ID {collection_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update collection"
        )


@collection_router.get("/children_list/{collection_id}", status_code=status.HTTP_200_OK)
async def collection_children_list(
        user: Annotated[Auth.AuthorizedUser, Depends(Auth.authorized_user())],
        sql_session: Annotated[SQL.AsyncSession, Depends(SQL.get_async_session)],
        collection_id: int,
):
    try:
        operation_list = await get_collection_operations_list_in_collection(sql_session, collection_id)
        result_list = []
        for operation in operation_list:
            single_operation = CollectionOperationList(
                child_id=operation[0],
                requester_name=operation[1],
                requester_surname=operation[2],
                operation=operation[3],
            )
            result_list.append(single_operation)
    except Exception as e:
        logger.logger.error(f"Error getting children status list: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get children status list"
        )

    if len(result_list)==0:
        raise HTTPException(status_code=204, detail="No operations found")
    return result_list


@collection_router.put("/{collection_id}/cancel", status_code=status.HTTP_200_OK, response_model=Collection)
async def cancel(
    user: Annotated[Auth.AuthorizedUser, Depends(Auth.authorized_user())],
    collection_id: int,
    sql_session: Annotated[SQL.AsyncSession, Depends(SQL.get_async_session)],
) -> Collection:
    try:
        return await collection_service.cancel(sql_session, collection_id, user)
    except Exception as e:
        logger.logger.error(f"Error canceling collection ID {collection_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel collection"
        )


@collection_router.delete("/{collection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    user: Annotated[Auth.AuthorizedUser, Depends(Auth.authorized_user(ADMIN_USER))],
    collection_id: int,
    sql_session: Annotated[SQL.AsyncSession, Depends(SQL.get_async_session)],
):
    try:
        await collection_service.delete(sql_session, collection_id)
    except Exception as e:
        logger.error(f"Error deleting collection ID {collection_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete collection"
        )
