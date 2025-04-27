from typing import List, Optional, Sequence
from fastapi import logger
from sqlmodel import col, delete, select
import sqlmodel

import src.SQL as SQL
from src.SQL.Tables import ClassGroup, ParentGroupRole, Child


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


async def get_by_name(session: SQL.AsyncSession, name: str) -> Optional[ClassGroup]:
    """Get a specific class group by name"""
    query = select(ClassGroup).where(ClassGroup.name == name)
    result = await session.exec(query)
    return result.first()


async def get_by_belonging_user(session: SQL.AsyncSession, user_id: int) -> Optional[Sequence[ClassGroup]]:
    """Get a specific class groups which user belongs to"""
    query = SQL.select(SQL.Tables.ClassGroup).join(
        SQL.Tables.ParentGroupRole, SQL.Tables.ParentGroupRole.class_group_id == SQL.Tables.ClassGroup.id).join(
        SQL.Tables.Parent, SQL.Tables.Parent.id == SQL.Tables.ParentGroupRole.parent_id).filter(
        SQL.Tables.Parent.account_id == user_id
    ).order_by(SQL.Tables.ClassGroup.id.desc())

    class_groups = await session.exec(query)
    class_groups_result = class_groups.all()
    if class_groups_result  is None:
        return None
    return class_groups_result


async def update(session: SQL.AsyncSession, class_group_id: int, updated_class_group: ClassGroup) -> Optional[ ClassGroup]:
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
      
      
async def delete(session: SQL.AsyncSession, class_group_id: int):
    """Delete a class group and manage related entities."""
    try:
        delete_parent_group_roles_query = sqlmodel.delete(ParentGroupRole).where(
            ParentGroupRole.class_group_id == class_group_id
        )
        await session.exec(delete_parent_group_roles_query)
        
        childs_query = select(Child).where(Child.group_id == class_group_id)
        childs = (await session.exec(childs_query)).all()
        for child in childs:
            child.group_id = None
            session.add(child)

        db_class_group = await get_by_id(session, class_group_id)
        session.delete(db_class_group)
        
        await session.commit()
    except Exception as e:
        logger.logger.error(e)
        await session.rollback()
        raise e

