from src.repository import collection_repository, class_group_repository, bank_account_repository
import src.SQL as SQL

from fastapi import HTTPException, status
from src.SQL.Tables import Collection
from src.Model import CollectionStatusEnum


async def create(
    sql_session: SQL.AsyncSession, owner_id: int, collection_data: Collection
) -> Collection:
    class_group = await class_group_repository.get_by_id(
        sql_session, collection_data.get('class_group_id')
    )
    if not class_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class group does not exist"
        )
        
    bank_account = await bank_account_repository.get_by_id(
        sql_session, collection_data['bank_account_id']
    )
    if not bank_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bank account does not exist"
        )
    
    collection_data.owner_id = owner_id
    
    return await collection_repository.create(sql_session, collection_data)


async def update(
    sql_session: SQL.AsyncSession, collection_id: int, update_data: Collection
) -> Collection:
    collection = await collection_repository.get_by_id(sql_session, collection_id)
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found"
        )
        
    collection = await collection_repository.get_by_id(sql_session, collection_id)
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found"
        )
    
    if collection.status != CollectionStatusEnum.OPEN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot update collection with a status other than OPEN"
        )
    
    return await collection_repository.update(sql_session, collection_id, update_data)


async def cancel(
    sql_session: SQL.AsyncSession, collection_id: int
) -> Collection:
    collection = await collection_repository.get_by_id(sql_session, collection_id)
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found"
        )
    
    if collection.status != CollectionStatusEnum.OPEN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel collection with a status other than OPEN"
        )
    
    collection.status = CollectionStatusEnum.CANCELLED
    return await collection_repository.update(sql_session, collection_id, collection)


async def delete(
    sql_session: SQL.AsyncSession, collection_id: int
):
    collection = await collection_repository.get_by_id(sql_session, collection_id)
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found"
        )
    
    if collection.status != CollectionStatusEnum.OPEN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete collection with a status other than OPEN"
        )

    await collection_repository.delete(sql_session, collection_id)
