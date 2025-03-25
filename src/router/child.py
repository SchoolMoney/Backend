from typing import Annotated, List, Optional, Sequence
from fastapi import APIRouter, Depends, HTTPException, Query, status

import src.SQL as SQL
from src.Model.ChildModel import ChildCreate, ChildBatchUpdate, ChildUpdate
from src.SQL.Enum.Privilege import ADMIN_USER
from src.SQL.Tables import Child
from src.Service import Auth
from src.repository import child_repository

child_router = APIRouter(prefix="/child", tags=["child"])


@child_router.get("/", status_code=status.HTTP_200_OK, response_model=List[Child])
async def get_children(
        user: Annotated[Auth.AuthorizedUser, Depends(Auth.authorized_user())],
        sql_session: Annotated[SQL.AsyncSession, Depends(SQL.get_async_session)],
        skip: int = 0,
        limit: int = 100,
        ids: Optional[List[int]] = Query(None),
        group_ids: Optional[List[int]] = Query(None)
) -> Sequence[Child]:
    """Get multiple children. Can filter by IDs, group_id or get all with pagination."""
    try:
        return await child_repository.get_all(sql_session, skip, limit, ids, group_ids)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve children"
        )


@child_router.get("/{child_id}", status_code=status.HTTP_200_OK, response_model=Child)
async def get_child(
        user: Annotated[Auth.AuthorizedUser, Depends(Auth.authorized_user())],
        child_id: int,
        sql_session: Annotated[SQL.AsyncSession, Depends(SQL.get_async_session)],
) -> Child:
    """Get a specific child by ID"""
    try:
        child = await child_repository.get_by_id(sql_session, child_id)
        if not child:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Child with ID {child_id} not found"
            )
        return child
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve child"
        )


@child_router.post("/", response_model=Child, status_code=status.HTTP_201_CREATED)
async def create_child(
        user: Annotated[Auth.AuthorizedUser, Depends(Auth.authorized_user())],
        child_data: ChildCreate,
        sql_session: Annotated[SQL.AsyncSession, Depends(SQL.get_async_session)],
) -> Child:
    """Create a new child"""
    if user.user_privilege != ADMIN_USER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to create a class group")

    try:
        # Create Child object from validated data
        child = Child(**child_data.model_dump())
        return await child_repository.create(sql_session, child)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid data: {str(e)}"
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create child"
        )


@child_router.put("/batch", status_code=status.HTTP_200_OK, response_model=List[Child])
async def update_many_children(
        user: Annotated[Auth.AuthorizedUser, Depends(Auth.authorized_user())],
        children_data: List[ChildBatchUpdate],
        sql_session: Annotated[SQL.AsyncSession, Depends(SQL.get_async_session)],
) -> List[Child]:
    """Update multiple children at once"""
    try:
        children = []
        for child_data in children_data:
            # Create Child object with ID
            child = Child(id=child_data.id, **child_data.model_dump(exclude={"id"}))
            children.append(child)

        updated_children = await child_repository.update_many(sql_session, children)
        return updated_children
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update children"
        )


@child_router.put("/{child_id}", status_code=status.HTTP_200_OK, response_model=Child)
async def update_child(
        user: Annotated[Auth.AuthorizedUser, Depends(Auth.authorized_user())],
        child_id: int,
        updated_data: ChildUpdate,
        sql_session: Annotated[SQL.AsyncSession, Depends(SQL.get_async_session)],
) -> Child:
    """Update an existing child"""
    try:
        # Create Child object from validated data (without ID)
        updated_child = Child(**updated_data.model_dump(exclude_unset=True))

        child = await child_repository.update(sql_session, child_id, updated_child)
        if not child:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Child with ID {child_id} not found"
            )
        return child
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update child"
        )


@child_router.delete("/{child_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_child(
        user: Annotated[Auth.AuthorizedUser, Depends(Auth.authorized_user())],
        child_id: int,
        sql_session: Annotated[SQL.AsyncSession, Depends(SQL.get_async_session)],
) -> None:
    """Delete a child"""
    if user.user_privilege != ADMIN_USER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to create a class group")

    try:
        deleted = await child_repository.delete(sql_session, child_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Child with ID {child_id} not found"
            )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete child"
        )
