from datetime import datetime
from typing import List, Optional, Sequence
from fastapi import logger
from sqlmodel import col, select

import src.SQL as SQL
from src.Model.UserAccountPrivilegeEnum import UserAccountPrivilegeEnum
from src.SQL.Tables import Collection, ClassGroup, ParentGroupRole
from src.SQL.Tables.People import Parent, UserAccount, Child
import src.SQL.Tables as CollectionStatusEnum
from src.SQL.Tables.Collection import CollectionOperation
from src.SQL.Enum.CollectionStatus import CANCELLED


async def get(
    session: SQL.AsyncSession,
    requester_privilege: int,
    requester_id: Optional[int] = None,
    name: Optional[str] = None,
    start_date_from: Optional[datetime] = None,
    start_date_to: Optional[datetime] = None,
    end_date_from: Optional[datetime] = None,
    end_date_to: Optional[datetime] = None,
    status: Optional[CollectionStatusEnum] = None,

) -> Sequence[Collection]:
    if requester_privilege == UserAccountPrivilegeEnum.ADMIN_USER:
        query = select(Collection).where(
            (Collection.name == name if name is not None else True),
            (
                Collection.start_date >= start_date_from
                if start_date_from is not None
                else True
            ),
            (Collection.start_date <= start_date_to if start_date_to is not None else True),
            (Collection.end_date >= end_date_from if end_date_from is not None else True),
            (Collection.end_date <= end_date_to if end_date_to is not None else True),
            (Collection.status == status if status is not None else True),
        )
    elif requester_privilege != UserAccountPrivilegeEnum.ADMIN_USER and requester_id is None:
        raise ValueError("When user is not an admin user request id is needed to be passed as parameter")
    else:
        query = select(Collection).join(
            ClassGroup, ClassGroup.id == Collection.class_group_id
        ).join(
            ParentGroupRole, ParentGroupRole.class_group_id == ClassGroup.id
        ).join(
           Parent, Parent.id == ParentGroupRole.parent_id
        ).join(
            UserAccount, UserAccount.id == Parent.account_id
        ).where(
            (Collection.name == name if name is not None else True),
            (
                Collection.start_date >= start_date_from
                if start_date_from is not None
                else True
            ),
            (Collection.start_date <= start_date_to if start_date_to is not None else True),
            (Collection.end_date >= end_date_from if end_date_from is not None else True),
            (Collection.end_date <= end_date_to if end_date_to is not None else True),
            (Collection.status == status if status is not None else True),
            UserAccount.id == requester_id
        )

    logger.logger.info(f"Handling collections query: {query}")

    results = await session.exec(query)
    return results.all()


async def get_by_id(
    session: SQL.AsyncSession, collection_id: int
) -> Optional[Collection]:
    query = select(Collection).where(Collection.id == collection_id)
    result = await session.exec(query)

    return result.first()

async def get_collection_operations_list_in_collection(
    session: SQL.AsyncSession,
    collection_id: int
):
    query = select(Child.id,
                   Parent.name,
                   Parent.surname,
                   CollectionOperation.operation_type
    ).select_from(Collection).join(
        CollectionOperation, Collection.id == CollectionOperation.collection_id
    ).join(
        Child, Child.id == CollectionOperation.child_id
    ).join(
        Parent, Parent.id == CollectionOperation.requester_id
    ).filter(
        Collection.id == collection_id,
    )
    try:
        db_response = await session.exec(query)
        query_result = db_response.all()
    except Exception as e:
        logger.logger.error(f"Failed to get children status list: {e}")
        raise e

    return query_result




async def create(session: SQL.AsyncSession, collection: Collection) -> Collection:
    try:
        session.add(collection)
        await session.commit()
        await session.refresh(collection)
        return collection
    except Exception as e:
        await session.rollback()
        raise e


async def update(
    session: SQL.AsyncSession, collection_id: int, updated_collection: Collection
) -> Optional[Collection]:
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

        db_collection.status = CANCELLED

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
