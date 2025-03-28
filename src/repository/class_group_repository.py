from typing import List, Optional, Sequence
from sqlmodel import col, select

import src.SQL as SQL
from src.SQL.Tables import ClassGroup


async def create(session: SQL.AsyncSession, class_group: ClassGroup) -> ClassGroup:
    """Create a new class group"""
    try:
        session.add(class_group)
        await session.commit()
        await session.refresh(class_group)
        return class_group
    except Exception as e:
        await session.rollback()
        raise e


async def get_all(
        session: SQL.AsyncSession,
        skip: int = 0,
        limit: int = 100,
        ids: Optional[List[int]] = None
) -> Sequence[ClassGroup]:
    """Get multiple class groups with optional filtering"""
    query = select(ClassGroup)

    if ids:
        query = query.where(col(ClassGroup.id).in_(ids))

    query = query.offset(skip).limit(limit)
    results = await session.exec(query)
    return results.all()


async def get_by_id(session: SQL.AsyncSession, class_group_id: int) -> Optional[ClassGroup]:
    """Get a specific class group by ID"""
    query = select(ClassGroup).where(ClassGroup.id == class_group_id)
    result = await session.exec(query)
    return result.first()


async def update(session: SQL.AsyncSession, class_group_id: int, updated_class_group: ClassGroup) -> Optional[
    ClassGroup]:
    """Update an existing class group"""
    try:
        db_class_group = await get_by_id(session, class_group_id)
        if not db_class_group:
            return None

        update_data = updated_class_group.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_class_group, key, value)

        session.add(db_class_group)
        await session.commit()
        await session.refresh(db_class_group)
        return db_class_group
    except Exception as e:
        await session.rollback()
        raise e


async def delete(session: SQL.AsyncSession, class_group_id: int) -> bool:
    """Delete a class group"""
    try:
        db_class_group = await get_by_id(session, class_group_id)
        if not db_class_group:
            return False

        await session.delete(db_class_group)
        await session.commit()
        return True
    except Exception as e:
        await session.rollback()
        raise e
