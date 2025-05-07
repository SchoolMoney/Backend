import asyncio
from typing import Optional, Sequence

import src.SQL as SQL
from src.SQL.Tables import ClassGroup, People, ParentGroupRole
from src.SQL.Tables.Collection import Collection
from src.SQL.Enum import CollectionStatus

import src.repository.class_group_repository as class_group_repository


class_view_response_model = {
    "class_group": ClassGroup,
    "children": Sequence[People.Child],
    "parents": [
        {"id": int, "name": str, "surname": str, "role": int, "account_id": int}
    ],
    "collections": Sequence[Collection],
}


async def get_children_in_class(
    session: SQL.AsyncSession, class_id: int
) -> Optional[Sequence[People.Child]]:
    """Get children assigned to a class with given id"""

    query = (
        SQL.select(People.Child)
        .join(ClassGroup, People.Child.group_id == ClassGroup.id)
        .filter(ClassGroup.id == class_id)
        .order_by(People.Child.surname)
    )

    children_list = await session.exec(query)
    children_result = children_list.all()
    await session.close()
    if children_result is None:
        return None
    return children_result


async def get_parents_in_class(
    session: SQL.AsyncSession, class_id: int
) -> Optional[Sequence[dict]]:
    """Get parents whose children are assigned to a class with given id"""

    query = (
        SQL.select(
            People.Parent.id,
            People.Parent.name,
            People.Parent.surname,
            ParentGroupRole.role,
            People.Parent.account_id,
        )
        .join(ParentGroupRole, People.Parent.id == ParentGroupRole.parent_id)
        .join(ClassGroup, ParentGroupRole.class_group_id == ClassGroup.id)
        .filter(ClassGroup.id == class_id)
        .order_by(People.Parent.surname)
    )

    parents_list = await session.exec(query)
    parents_result = parents_list.all()
    formatted_parents = [
        {
            "id": parent[0],
            "name": parent[1],
            "surname": parent[2],
            "role": parent[3],
            "account_id": parent[4],
        }
        for parent in parents_result
    ]
    await session.close()
    if not formatted_parents:
        return []

    return formatted_parents


async def get_collections_in_class(
    session: SQL.AsyncSession, class_id: int, status: CollectionStatus
) -> Optional[Sequence[Collection]]:
    """Get collection which belongs to a class with given id and has specified status"""

    query = (
        SQL.select(Collection)
        .join(ClassGroup, ClassGroup.id == Collection.class_group_id)
        .filter(ClassGroup.id == class_id, Collection.status == status)
    )

    collections_list = await session.exec(query)
    collections_result = collections_list.all()
    await session.close()
    if collections_result is None:
        return None

    return collections_result


async def get_requester_information(
    session: SQL.AsyncSession, class_id: int, user_id: int
) -> Optional[dict]:
    """Get information about a requester"""

    query = (
        SQL.select(
            People.Parent.id,
            People.Parent.name,
            People.Parent.surname,
            ParentGroupRole.role,
        )
        .join(ParentGroupRole, People.Parent.id == ParentGroupRole.parent_id)
        .join(People.UserAccount, People.Parent.account_id == People.UserAccount.id)
        .filter(
            ParentGroupRole.class_group_id == class_id, People.UserAccount.id == user_id
        )
    )

    requester_data = await session.exec(query)
    requester_record = requester_data.first()
    await session.close()
    if requester_record is None:
        return None
    return {
        "parent_id": requester_record[0],
        "name": requester_record[1],
        "surname": requester_record[2],
        "group_role": requester_record[3],
    }


async def collect_class_view_data(
    class_id: int, status: CollectionStatus, user_id: int
) -> dict:
    """Collect data for class view by running all queries concurrently"""

    children, parents, collections, class_group, requester = await asyncio.gather(
        get_children_in_class(await SQL.get_async_session(), class_id),
        get_parents_in_class(await SQL.get_async_session(), class_id),
        get_collections_in_class(await SQL.get_async_session(), class_id, status),
        class_group_repository.get_by_id(await SQL.get_async_session(), class_id),
        get_requester_information(await SQL.get_async_session(), class_id, user_id),
    )

    return {
        "class": class_group.model_dump() if class_group else None,
        "children": [child.model_dump() for child in children],
        "parents": parents,
        "collections": [collection.model_dump() for collection in collections],
        "requester": requester,
    }
