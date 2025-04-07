from datetime import datetime
from typing import List, Optional, Sequence
from fastapi import logger
from sqlmodel import col, select

import src.SQL as SQL
from src.SQL.Tables import Collection
import src.SQL.Tables as CollectionStatusEnum


async def get(
    session: SQL.AsyncSession,
    name: Optional[str] = None,
    start_date_from: Optional[datetime] = None,
    start_date_to: Optional[datetime] = None,
    end_date_from: Optional[datetime] = None,
    end_date_to: Optional[datetime] = None,
    status: Optional[CollectionStatusEnum] = None
) -> Sequence[Collection]:
    query = select(Collection).where(
        (Collection.name == name if name is not None else True),
        (Collection.start_date >= start_date_from if start_date_from is not None else True),
        (Collection.start_date <= start_date_to if start_date_to is not None else True),
        (Collection.end_date >= end_date_from if end_date_from is not None else True),
        (Collection.end_date <= end_date_to if end_date_to is not None else True),
        (Collection.status == status if status is not None else True),
    )
    
    logger.logger.info(f'Handling collections query: {query}')

    results = await session.exec(query)
    return results.all()


async def get_by_id(session: SQL.AsyncSession, collection_id: int) -> Optional[Collection]:
    query = select(Collection).where(Collection.id == collection_id)
    result = await session.exec(query)
    
    return result.first()


async def create(session: SQL.AsyncSession, collection: Collection) -> Collection:
    try:
        session.add(collection)
        await session.commit()
        await session.refresh(collection)
        return collection
    except Exception as e:
        await session.rollback()
        raise e


async def update(session: SQL.AsyncSession, collection_id: int, updated_collection: Collection) -> Optional[Collection]:
    try:
        db_collection = await get_by_id(session, collection_id)
        if not db_collection:
            return None

        update_data = updated_collection.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_collection, key, value)

        session.add(db_collection)
        await session.commit()
        await session.refresh(db_collection)
        return db_collection
    except Exception as e:
        await session.rollback()
        raise e


async def cancel(session: SQL.AsyncSession, collection_id: int) -> Optional[Collection]:
    try:
        db_collection = await get_by_id(session, collection_id)
        if not db_collection:
            return None
            
        db_collection.status = CollectionStatus.CANCELLED

        session.add(db_collection)
        await session.commit()
        await session.refresh(db_collection)
        return db_collection
    except Exception as e:
        await session.rollback()
        raise e


async def delete(session: SQL.AsyncSession, collection_id: int) -> bool:
    try:
        db_class_collection = await get_by_id(session, collection_id)
        if not db_class_collection:
            return False

        await session.delete(db_class_collection)
        await session.commit()
        return True
    except Exception as e:
        await session.rollback()
        raise e
