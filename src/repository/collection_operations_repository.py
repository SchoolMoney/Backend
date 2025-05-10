from typing import Sequence
from fastapi import logger
from sqlmodel import select
from src.SQL import AsyncSession
from src.SQL.Tables.Collection import CollectionOperation
from src.SQL.Tables.People import Parent, Child, UserAccount, User
from src.Model.CollectionOperation import CollectionOperationMetadata

async def get(session: AsyncSession, collection_id: int) -> Sequence[CollectionOperationMetadata]:
    query = (
        select(CollectionOperation, UserAccount, Parent, Child)
        .join(CollectionOperation, CollectionOperation.requester_id == UserAccount.id)
        .join(Parent, Parent.account_id == UserAccount.id)
        .join(Child, CollectionOperation.child_id == Child.id)
        .filter(CollectionOperation.collection_id == collection_id)
    )

    try:
        results = await session.exec(query)
        records = results.all()
        metadata_list = []
        for operation, user_account, parent, child in records:
            metadata_list.append(CollectionOperationMetadata(
                collection_id=operation.collection_id,
                
                child_id=operation.child_id,
                child_name=child.name,            # retrieved from Child table
                child_surname=child.surname,      # retrieved from Child table
                
                requestor_id=operation.requester_id,
                requestor_name=parent.name,       # retrieved from Parent table
                requestor_surname=parent.surname, # retrieved from Parent table
                
                operation_date=operation.operation_date,
                operation_type=operation.operation_type  # include if needed; adjust if not present
            ))
        return metadata_list
    except Exception as error:
        logger.logger.error(error)
        raise error
