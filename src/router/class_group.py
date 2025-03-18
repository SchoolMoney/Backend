from typing import Annotated, List, Optional, Sequence
from fastapi import APIRouter, Depends, HTTPException, Query, status

import src.SQL as SQL
from src.SQL.Tables import ClassGroup
from src.repository import class_group_repository

class_group_router = APIRouter(prefix="/class_group", tags=["class_group"])


@class_group_router.get("/", status_code=status.HTTP_200_OK, response_model=List[ClassGroup])
async def get_class_groups(
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
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve class groups"
        )


@class_group_router.get("/{class_group_id}", status_code=status.HTTP_200_OK, response_model=ClassGroup)
async def get_class_group(
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
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve class group"
        )


@class_group_router.post("/", response_model=ClassGroup, status_code=status.HTTP_201_CREATED)
async def create_class_group(
        class_group: ClassGroup,
        sql_session: Annotated[SQL.AsyncSession, Depends(SQL.get_async_session)],
) -> ClassGroup:
    """Create a new class group"""
    try:
        return await class_group_repository.create(sql_session, class_group)
    except HTTPException:
        raise  # Re-raise HTTPException as is
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create class group"
        )


@class_group_router.put("/{class_group_id}", status_code=status.HTTP_200_OK, response_model=ClassGroup)
async def update_class_group(
        class_group_id: int,
        updated_class_group: ClassGroup,
        sql_session: Annotated[SQL.AsyncSession, Depends(SQL.get_async_session)],
) -> ClassGroup:
    """Update an existing class group"""
    try:
        class_group = await class_group_repository.update(sql_session, class_group_id, updated_class_group)
        if not class_group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Class group with ID {class_group_id} not found"
            )
        return class_group
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update class group"
        )


@class_group_router.delete("/{class_group_id}", status_code=status.HTTP_200_OK)
async def delete_class_group(
        class_group_id: int,
        sql_session: Annotated[SQL.AsyncSession, Depends(SQL.get_async_session)],
) -> None:
    """Delete a class group"""
    try:
        deleted = await class_group_repository.delete(sql_session, class_group_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Class group with ID {class_group_id} not found"
            )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete class group"
        )
