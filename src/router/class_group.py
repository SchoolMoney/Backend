from typing import Annotated, List, Optional, Sequence
from fastapi import APIRouter, Depends, HTTPException, Query, logger, status

from src.Service.ClassGroup import class_group_service
from src.Model.ClassGroup import AddClassGroup, UpdateClassGroup, ChangeClassGroupCashier
import src.SQL as SQL
from src.Model.CollectionStatusEnum import CollectionStatusEnum
from src.SQL.Enum.Privilege import ADMIN_USER
from src.SQL.Tables import ClassGroup
from src.Service import Auth
from src.repository import class_group_repository
from src.repository.class_group_repository import get_by_belonging_user
from src.Service.ClassView import class_view_operations

class_group_router = APIRouter(tags=["class_group"])


@class_group_router.get("/", status_code=status.HTTP_200_OK, response_model=List[ClassGroup])
async def get_class_groups(
    user: Annotated[Auth.AuthorizedUser, Depends(Auth.authorized_user())],
    sql_session: Annotated[SQL.AsyncSession, Depends(SQL.get_async_session)],
    skip: int = 0,
    limit: int = 100,
    ids: Optional[List[int]] = Query(None),
) -> Sequence[ClassGroup]:
    """Get multiple class groups. Can filter by IDs or get all with pagination."""
    try:
        return await class_group_repository.get_all(sql_session, skip, limit, ids)
    except HTTPException:
        raise
    except Exception as e:
        logger.logger.error(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve class groups"
        )


@class_group_router.get("/list-class-groups", status_code=status.HTTP_200_OK)
async def get_user_class_groups(
        user: Annotated[Auth.AuthorizedUser, Depends(Auth.authorized_user())],
        sql_session: Annotated[SQL.AsyncSession, Depends(SQL.get_async_session)],
) -> Sequence[ClassGroup]:
    """Get all user class groups which he belongs to"""
    query_result = await get_by_belonging_user(sql_session, user.user_id)
    if not query_result:
        raise HTTPException(
            status_code=status.HTTP_204_NO_CONTENT,
            detail="You have no children in any class"
        )
    return query_result


@class_group_router.get("/{class_group_id}", status_code=status.HTTP_200_OK, response_model=ClassGroup)
async def get_class_group(
        user: Annotated[Auth.AuthorizedUser, Depends(Auth.authorized_user())],
        class_group_id: int,
        sql_session: Annotated[SQL.AsyncSession, Depends(SQL.get_async_session)],
) -> ClassGroup:
    """Get a specific class group by ID"""
    try:
        class_group = await class_group_repository.get_by_id(sql_session, class_group_id)
        if not class_group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Class group with ID {class_group_id} not found"
            )
        return class_group
    except HTTPException:
        raise
    except Exception as e:
        logger.logger.error(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve class group"
        )


@class_group_router.post("/", status_code=status.HTTP_201_CREATED, response_model=ClassGroup)
async def create_class_group(
        user: Annotated[Auth.AuthorizedUser, Depends(Auth.authorized_user())],
        request: AddClassGroup,
        sql_session: Annotated[SQL.AsyncSession, Depends(SQL.get_async_session)],
) -> ClassGroup:
    """Create a new class group"""
    try:
        return await class_group_service.create(sql_session, request, user.user_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.logger.error(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create class group"
        )


@class_group_router.put("/{class_group_id}", status_code=status.HTTP_200_OK)
async def update_class_group(
        user: Annotated[Auth.AuthorizedUser, Depends(Auth.authorized_user())],
        class_group_id: int,
        request: UpdateClassGroup,
        sql_session: Annotated[SQL.AsyncSession, Depends(SQL.get_async_session)],
):
    """Update an existing class group"""
    try:
        await class_group_service.update(sql_session, class_group_id, request, user.user_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.logger.error(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update class group"
        )


@class_group_router.put("/{class_group_id}/cashier", status_code=status.HTTP_204_NO_CONTENT)
async def change_class_group_cashier(
    user: Annotated[Auth.AuthorizedUser, Depends(Auth.authorized_user(ADMIN_USER))],
    class_group_id: int,
    request: ChangeClassGroupCashier,
    sql_session: Annotated[SQL.AsyncSession, Depends(SQL.get_async_session)],
) -> None:
    try:            
        await class_group_service.change_cashier(sql_session, class_group_id, request)
    except HTTPException:
        raise
    except Exception as e:
        logger.logger.error(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update class group cashier"
        )


@class_group_router.delete("/{class_group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_class_group(
        user: Annotated[Auth.AuthorizedUser, Depends(Auth.authorized_user())],
        class_group_id: int,
        sql_session: Annotated[SQL.AsyncSession, Depends(SQL.get_async_session)],
) -> None:
    """Delete a class group"""
    try:
        await class_group_service.delete(sql_session, class_group_id, user.user_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.logger.error(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete class group"
        )


@class_group_router.get("/class-view/{class_group_id}", status_code=status.HTTP_200_OK)
async def get_class_view(
        user: Annotated[Auth.AuthorizedUser, Depends(Auth.authorized_user())],
        class_group_id: int,
        collection_status: CollectionStatusEnum = Query(
            default=CollectionStatusEnum.OPEN,
            description="Status kolekcji: 0=OPEN, 1=FINISHED, 2=NOT_PAID_BEFORE_DEADLINE, 3=CANCELLED"
        )
):
    """Get a specific class view by ID"""
    class_view_data = await class_view_operations.collect_class_view_data(
        class_group_id,
        int(collection_status),
        user.user_id
    )

    if not class_view_data["class"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Class view not found"
        )

    parent_account_ids = [parent['account_id'] for parent in class_view_data["parents"]]
    if user.user_id not in parent_account_ids and user.user_privilege!=ADMIN_USER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User not allowed to view this class"
        )
    return class_view_data

