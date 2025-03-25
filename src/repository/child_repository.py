from typing import List, Optional, Sequence
from sqlmodel import col, select

import src.SQL as SQL
from src.SQL.Tables import Child


async def create(session: SQL.AsyncSession, child: Child) -> Child:
    """Create a new child"""
    try:
        session.add(child)
        await session.commit()
        await session.refresh(child)
        return child
    except Exception as e:
        await session.rollback()
        raise e


async def get_all(
        session: SQL.AsyncSession,
        skip: int = 0,
        limit: int = 100,
        ids: Optional[List[int]] = None,
        group_ids: Optional[List[int]] = None
) -> Sequence[Child]:
    """Get multiple children with optional filtering"""
    query = select(Child)

    if ids:
        query = query.where(col(Child.id).in_(ids))

    if group_ids:
        query = query.where(col(Child.group_id).in_(group_ids))

    query = query.offset(skip).limit(limit)
    results = await session.exec(query)
    return results.all()


async def get_by_id(session: SQL.AsyncSession, child_id: int) -> Optional[Child]:
    """Get a specific child by ID"""
    query = select(Child).where(Child.id == child_id)
    result = await session.exec(query)
    return result.first()


async def update(session: SQL.AsyncSession, child_id: int, updated_child: Child) -> Optional[Child]:
    """Update an existing child"""
    try:
        db_child = await get_by_id(session, child_id)
        if not db_child:
            return None

        update_data = updated_child.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_child, key, value)

        session.add(db_child)
        await session.commit()
        await session.refresh(db_child)
        return db_child
    except Exception as e:
        await session.rollback()
        raise e


async def update_many(session: SQL.AsyncSession, children: List[Child]) -> List[Child]:
    """Update multiple children at once"""
    try:
        updated_children = []
        for child in children:
            if not hasattr(child, 'id') or child.id is None:
                continue  # Skip children without IDs

            db_child = await get_by_id(session, child.id)
            if not db_child:
                continue  # Skip children that don't exist

            update_data = child.dict(exclude_unset=True)
            for key, value in update_data.items():
                if key != 'id' and value  is not None:  # Don't update the ID
                    setattr(db_child, key, value)

            session.add(db_child)
            updated_children.append(db_child)

        await session.commit()
        for child in updated_children:
            await session.refresh(child)

        return updated_children
    except Exception as e:
        await session.rollback()
        raise e


async def delete(session: SQL.AsyncSession, child_id: int) -> bool:
    """Delete a child"""
    try:
        db_child = await get_by_id(session, child_id)
        if not db_child:
            return False

        await session.delete(db_child)
        await session.commit()
        return True
    except Exception as e:
        await session.rollback()
        raise e
