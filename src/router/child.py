from typing import Annotated, List, Optional, Sequence
from fastapi import APIRouter, Depends, HTTPException, Query, status
from datetime import date as datetime_date

import src.SQL as SQL
from src.SQL.Tables import Child
from src.repository import child_repository

child_router = APIRouter(prefix="/child", tags=["child"])


@child_router.get("/", status_code=status.HTTP_200_OK, response_model=List[Child])
async def get_children(
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
        child_data: dict,
        sql_session: Annotated[SQL.AsyncSession, Depends(SQL.get_async_session)],
) -> Child:
    """Create a new child"""
    try:
        if isinstance(child_data.get("birth_date"), str):
            child_data["birth_date"] = datetime_date.fromisoformat(child_data["birth_date"])

        # Create Child object from processed data
        child = Child(**child_data)
        return await child_repository.create(sql_session, child)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD"
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create child"
        )


@child_router.put("/batch", status_code=status.HTTP_200_OK, response_model=List[Child])
async def update_many_children(
        children_data: List[dict],
        sql_session: Annotated[SQL.AsyncSession, Depends(SQL.get_async_session)],
) -> List[Child]:
    """Update multiple children at once"""
    try:
        children = []
        for child_data in children_data:
            # Convert the string date to a proper date object if present
            if "birth_date" in child_data and isinstance(child_data["birth_date"], str):
                child_data["birth_date"] = datetime_date.fromisoformat(child_data["birth_date"])

            # Create Child object
            child = Child(**child_data)
            children.append(child)

        updated_children = await child_repository.update_many(sql_session, children)
        return updated_children
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD"
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update children"
        )


@child_router.put("/{child_id}", status_code=status.HTTP_200_OK, response_model=Child)
async def update_child(
        child_id: int,
        updated_data: dict,
        sql_session: Annotated[SQL.AsyncSession, Depends(SQL.get_async_session)],
) -> Child:
    """Update an existing child"""
    try:
        # Convert the string date to a proper date object if present
        if "birth_date" in updated_data and isinstance(updated_data["birth_date"], str):
            updated_data["birth_date"] = datetime_date.fromisoformat(updated_data["birth_date"])

        # Create Child object
        updated_child = Child(**updated_data)

        child = await child_repository.update(sql_session, child_id, updated_child)
        if not child:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Child with ID {child_id} not found"
            )
        return child
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD"
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update child"
        )


@child_router.delete("/{child_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_child(
        child_id: int,
        sql_session: Annotated[SQL.AsyncSession, Depends(SQL.get_async_session)],
) -> None:
    """Delete a child"""
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
