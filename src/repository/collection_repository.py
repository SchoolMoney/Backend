import asyncio
from datetime import datetime
from typing import List, Optional, Sequence
from fastapi import logger
from sqlmodel import select, and_, func

from src.repository import collection_operations_repository
import src.SQL as SQL
from src.Model.CollectionModel import CollectionChildrenList
from src.Model.UserAccountPrivilegeEnum import UserAccountPrivilegeEnum
from src.SQL.Tables import Collection, ClassGroup, ParentGroupRole
from src.SQL.Tables.People import Parent, UserAccount, Child
import src.SQL.Tables as CollectionStatusEnum
from src.SQL.Tables.Collection import CollectionOperation
from src.SQL.Enum.CollectionStatus import CANCELLED
from src.Service.Auth import AuthorizedUser
import src.repository.collection_documents_repository as collection_documents_repository


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
            (
                Collection.start_date <= start_date_to
                if start_date_to is not None
                else True
            ),
            (
                Collection.end_date >= end_date_from
                if end_date_from is not None
                else True
            ),
            (Collection.end_date <= end_date_to if end_date_to is not None else True),
            (Collection.status == status if status is not None else True),
        )
    elif (
        requester_privilege != UserAccountPrivilegeEnum.ADMIN_USER
        and requester_id is None
    ):
        raise ValueError(
            "When user is not an admin user request id is needed to be passed as parameter"
        )
    else:
        query = (
            select(Collection)
            .join(ClassGroup, ClassGroup.id == Collection.class_group_id)
            .join(ParentGroupRole, ParentGroupRole.class_group_id == ClassGroup.id)
            .join(Parent, Parent.id == ParentGroupRole.parent_id)
            .join(UserAccount, UserAccount.id == Parent.account_id)
            .where(
                (Collection.name == name if name is not None else True),
                (
                    Collection.start_date >= start_date_from
                    if start_date_from is not None
                    else True
                ),
                (
                    Collection.start_date <= start_date_to
                    if start_date_to is not None
                    else True
                ),
                (
                    Collection.end_date >= end_date_from
                    if end_date_from is not None
                    else True
                ),
                (
                    Collection.end_date <= end_date_to
                    if end_date_to is not None
                    else True
                ),
                (Collection.status == status if status is not None else True),
                UserAccount.id == requester_id,
            )
        )

    logger.logger.info(f"Handling collections query: {query}")

    results = await session.exec(query)
    return results.all()


async def get_by_id(
    session: SQL.AsyncSession, collection_id: int
) -> Optional[Collection]:
    query = select(Collection).where(Collection.id == collection_id)
    result = await session.exec(query)
    await session.close()
    return result.first()


async def get_list_of_children_for_collection(
    session: SQL.AsyncSession, collection_id: int
) -> List[CollectionChildrenList]:
    latest_ops = (
        select(
            CollectionOperation.child_id,
            CollectionOperation.collection_id,
            func.max(CollectionOperation.operation_date).label("latest_date"),
        )
        .group_by(CollectionOperation.child_id, CollectionOperation.collection_id)
        .alias("latest_ops")
    )

    query = (
        select(
            Child.id,
            Child.name,
            Child.surname,
            Parent.name.label("parent_name"),
            Parent.surname.label("parent_surname"),
            CollectionOperation.operation_type,
            CollectionOperation.operation_date,
        )
        .join(ClassGroup, Child.group_id == ClassGroup.id)
        .join(Collection, Collection.class_group_id == ClassGroup.id)
        .outerjoin(
            latest_ops,
            (latest_ops.c.child_id == Child.id)
            & (latest_ops.c.collection_id == Collection.id),
        )
        .outerjoin(
            CollectionOperation,
            (CollectionOperation.child_id == latest_ops.c.child_id)
            & (CollectionOperation.collection_id == latest_ops.c.collection_id)
            & (CollectionOperation.operation_date == latest_ops.c.latest_date),
        )
        .outerjoin(Parent, Parent.id == CollectionOperation.requester_id)
        .where(Collection.id == collection_id)
    )
    try:
        query_result: Sequence = (await session.exec(query)).all()
    except Exception as e:
        logger.logger.error(f"Failed to get children status list: {e}")
        raise e
    finally:
        await session.close()

    result_list = []
    for operation in query_result:
        single_operation = CollectionChildrenList(
            child_id=operation[0],
            child_name=operation[1],
            child_surname=operation[2],
            requester_name=operation[3],
            requester_surname=operation[4],
            operation=operation[5],
            operation_date=operation[6],
        )
        result_list.append(single_operation)

    return result_list


async def gather_collection_view_data(collection_id: int, user: AuthorizedUser) -> dict:
    """Collect data for class view by running all queries concurrently"""

    collection, children, operations, operations = await asyncio.gather(
        get_by_id(session=await SQL.get_async_session(), collection_id=collection_id),
        get_list_of_children_for_collection(
            session=await SQL.get_async_session(), collection_id=collection_id
        ),
        collection_documents_repository.get(
            session=await SQL.get_async_session(), collection_id=collection_id
        ),
        collection_operations_repository.get(
            session=await SQL.get_async_session(), collection_id=collection_id
        ),
    )

    return {
        "collection": collection.model_dump(),
        "operations": [operation.model_dump() for operation in operations],
        "children": [child.model_dump() for child in children],
        "documents": [document.model_dump() for document in operations],
    }


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
