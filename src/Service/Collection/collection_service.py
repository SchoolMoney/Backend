from src.Model.CollectionModel import CreateCollection
from src.repository import collection_repository
import src.SQL as SQL
from src.Service import Auth
import src.SQL.Enum.ParentRole as ParentRole
from src.SQL.Enum.Privilege import ADMIN_USER

from fastapi import HTTPException, status
from src.SQL.Tables import Collection
from src.SQL.Enum import CollectionStatus
from src.Service.IBAN_generator import iban_db_service
from src.repository import (
    class_group_repository,
    account_repository,
    parent_group_role_repository,
    parent_repository,
)


async def create(
    sql_session: SQL.AsyncSession, owner_id: int, collection_data: CreateCollection
) -> Collection:
    class_group = await class_group_repository.get_by_id(
        sql_session, collection_data.class_group_id
    )
    if not class_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Class group does not exist"
        )

    bank_account = await iban_db_service.create_bank_account(sql_session)

    collection_data.owner_id = owner_id
    collection_data.bank_account_id = bank_account.id
    collection_data.status = CollectionStatus.OPEN

    collection = SQL.Tables.Collection(**collection_data.model_dump())

    return await collection_repository.create(sql_session, collection)


async def update(
    sql_session: SQL.AsyncSession, collection_id: int, update_data: Collection
) -> Collection:
    collection = await collection_repository.get_by_id(sql_session, collection_id)
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found"
        )

    if collection.status != CollectionStatus.OPEN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot update collection with a status other than OPEN",
        )

    return await collection_repository.update(sql_session, collection_id, update_data)


async def cancel(
    sql_session: SQL.AsyncSession, collection_id: int, user: Auth.AuthorizedUser
) -> Collection:
    collection = await collection_repository.get_by_id(sql_session, collection_id)
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found"
        )

    if collection.status != CollectionStatus.OPEN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel collection with a status other than OPEN",
        )

    account = await account_repository.get_by_user(sql_session, user.user_id)
    parent = await parent_repository.get_by_user_account(sql_session, account.id)

    parent_group_role = await parent_group_role_repository.get(
        sql_session, collection.class_group_id, parent.id
    )
    if (
        parent_group_role.role != ParentRole.CASHIER
        and user.user_privilege != ADMIN_USER
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only cashier can cancel collection",
        )

    return await collection_repository.cancel(sql_session, collection_id)


async def delete(sql_session: SQL.AsyncSession, collection_id: int):
    collection = await collection_repository.get_by_id(sql_session, collection_id)
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found"
        )

    if collection.status != CollectionStatus.OPEN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete collection with a status other than OPEN",
        )

    await collection_repository.delete(sql_session, collection_id)
