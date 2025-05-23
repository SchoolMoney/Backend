from datetime import date, datetime
from typing import Annotated, List, Optional, Sequence
from fastapi import APIRouter, Depends, HTTPException, Query, status, logger
from src.Model.CollectionModel import CreateCollection, UpdateCollection
import src.SQL as SQL
import src.SQL.Enum.CollectionStatus as CollectionStatus
from src.SQL.Enum import CollectionOperationType
from src.Model.CollectionStatusEnum import CollectionStatusEnum
from src.SQL.Enum.Privilege import ADMIN_USER
from src.SQL.Tables import Collection, Parent, ParentGroupRole
from src.SQL.Tables.Financial import BankAccountOperation
from src.Service import Auth
from src.Service.Collection import collection_service
from src.repository import (
    collection_repository,
    child_repository,
    bank_account_repository,
    parent_repository,
)
from src.repository.collection_repository import gather_collection_view_data
from src.Service.Collection.collection_validator import (
    check_if_user_can_view_collection,
)

collection_router = APIRouter()


@collection_router.get(
    "", status_code=status.HTTP_200_OK, response_model=List[Collection]
)
async def get(
    user: Annotated[Auth.AuthorizedUser, Depends(Auth.authorized_user())],
    sql_session: Annotated[SQL.AsyncSession, Depends(SQL.get_async_session)],
    name: Optional[str] = Query(None),
    start_date_from: Optional[date] = Query(None),
    start_date_to: Optional[date] = Query(None),
    end_date_from: Optional[date] = Query(None),
    end_date_to: Optional[date] = Query(None),
    collection_status: Optional[CollectionStatusEnum] = Query(None),
) -> Sequence[Collection]:
    try:
        return await collection_repository.get(
            sql_session,
            user.user_privilege,
            user.user_id,
            name,
            start_date_from,
            start_date_to,
            end_date_from,
            end_date_to,
            collection_status,
        )
    except ValueError as e:
        logger.logger.error(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
    except Exception as e:
        logger.logger.error(f"Error retrieving collections: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve collections",
        )


@collection_router.get(
    "/{collection_id}", status_code=status.HTTP_200_OK, response_model=Collection
)
async def get_by_id(
    user: Annotated[Auth.AuthorizedUser, Depends(Auth.authorized_user())],
    collection_id: int,
    sql_session: Annotated[SQL.AsyncSession, Depends(SQL.get_async_session)],
) -> Collection:
    try:
        return await collection_repository.get_by_id(sql_session, collection_id)
    except Exception as e:
        logger.logger.error(f"Error retrieving collection by ID {collection_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve collection",
        )


@collection_router.post(
    "", response_model=Collection, status_code=status.HTTP_201_CREATED
)
async def create(
    user: Annotated[Auth.AuthorizedUser, Depends(Auth.authorized_user())],
    collection: CreateCollection,
    sql_session: Annotated[SQL.AsyncSession, Depends(SQL.get_async_session)],
) -> Collection:
    try:
        parent_id = (
            await sql_session.exec(
                SQL.select(Parent.id).where(Parent.account_id == user.user_id)
            )
        ).first()
        return await collection_service.create(sql_session, parent_id, collection)
    except Exception as e:
        logger.logger.error(f"Error creating collection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create collection",
        )


@collection_router.put(
    "/{collection_id}", status_code=status.HTTP_200_OK, response_model=Collection
)
async def update(
    user: Annotated[Auth.AuthorizedUser, Depends(Auth.authorized_user())],
    collection_id: int,
    updated_collection: UpdateCollection,
    sql_session: Annotated[SQL.AsyncSession, Depends(SQL.get_async_session)],
) -> Collection:
    try:
        return await collection_service.update(
            sql_session, collection_id, updated_collection
        )
    except Exception as e:
        logger.logger.error(f"Error updating collection ID {collection_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update collection",
        )


@collection_router.get(
    "/collection-view/{collection_id}",
    status_code=status.HTTP_200_OK,
    response_model=dict,
)
async def collection_view(
    user: Annotated[Auth.AuthorizedUser, Depends(Auth.authorized_user())],
    sql_session: Annotated[SQL.AsyncSession, Depends(SQL.get_async_session)],
    collection_id: int,
):
    if (
        not await check_if_user_can_view_collection(
            sql_session, collection_id, user.user_id
        )
        and user.user_privilege != ADMIN_USER
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    try:
        collection_data = await gather_collection_view_data(collection_id, user)

        requester = (
            await sql_session.exec(
                SQL.select(Parent.id, Parent.name, Parent.surname, ParentGroupRole.role)
                .select_from(Collection)
                .join(
                    ParentGroupRole,
                    ParentGroupRole.class_group_id == Collection.class_group_id,
                )
                .join(Parent, Parent.id == ParentGroupRole.parent_id)
                .filter(
                    Parent.account_id == user.user_id,
                    Collection.id == collection_id,
                )
            )
        ).first()

        if requester:
            collection_data["requester"] = {
                "parent_id": requester[0],
                "name": requester[1],
                "surname": requester[2],
                "role": requester[3],
            }
    except Exception as e:
        logger.logger.error(f"Error retrieving collection view: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve collection view",
        )

    return collection_data


@collection_router.put(
    "/{collection_id}/pay/{child_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def pay(
    user: Annotated[Auth.AuthorizedUser, Depends(Auth.authorized_user())],
    collection_id: int,
    child_id: int,
    sql_session: Annotated[SQL.AsyncSession, Depends(SQL.get_async_session)],
) -> None:
    bank_account: SQL.Tables.BankAccount = (
        await sql_session.exec(
            SQL.select(SQL.Tables.BankAccount)
            .join(SQL.Tables.Parent)
            .where(SQL.Tables.Parent.account_id == user.user_id)
        )
    ).first()

    collection: SQL.Tables.Collection = (
        await sql_session.exec(
            SQL.select(SQL.Tables.Collection).where(
                SQL.Tables.Collection.id == collection_id
            )
        )
    ).first()

    if collection.status != CollectionStatus.OPEN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot pay for a collection with a status other than OPEN",
        )

    child: SQL.Tables.Child = await child_repository.get_by_id(sql_session, child_id)

    if collection.price > (await bank_account.get_balance(sql_session)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient funds",
        )
    payment = SQL.Tables.BankAccountOperation(
        amount=collection.price,
        title=f"Collection Payment - {collection.name}",
        description=f"Payment for child {child.name} {child.surname}",
        source_account_id=bank_account.id,
        destination_account_id=collection.bank_account_id,
    )
    try:
        sql_session.add(payment)
        await sql_session.commit()
        await sql_session.refresh(payment)
        sql_session.add(
            SQL.Tables.CollectionOperation(
                child_id=child_id,
                collection_id=collection_id,
                operation_type=CollectionOperationType.PAY,
                requester_id=user.user_id,
                payment_id=payment.operation_id,
            )
        )
        await sql_session.commit()
    except Exception:
        await sql_session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to pay for child",
        )


@collection_router.put(
    "/{collection_id}/unsubscribe/{child_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def unsubscribe(
    user: Annotated[Auth.AuthorizedUser, Depends(Auth.authorized_user())],
    collection_id: int,
    child_id: int,
    sql_session: Annotated[SQL.AsyncSession, Depends(SQL.get_async_session)],
) -> None:
    parents: list[SQL.Tables.Parent] = (
        await sql_session.exec(
            SQL.select(SQL.Tables.Parent)
            .join(SQL.Tables.Parenthood)
            .where(SQL.Tables.Parenthood.child_id == child_id)
        )
    ).all()

    if user.user_id not in [parent.account_id for parent in parents]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to unsubscribe this child",
        )

    collection: SQL.Tables.Collection = (
        await sql_session.exec(
            SQL.select(SQL.Tables.Collection).where(
                SQL.Tables.Collection.id == collection_id
            )
        )
    ).first()

    if collection.status != CollectionStatus.OPEN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot unsubscribe from a collection with a status other than OPEN",
        )

    try:
        sql_session.add(
            SQL.Tables.CollectionOperation(
                child_id=child_id,
                collection_id=collection_id,
                operation_type=CollectionOperationType.DISCHARGE,
                requester_id=user.user_id,
            )
        )
        await sql_session.commit()
    except Exception:
        await sql_session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to unsubscribe child",
        )


@collection_router.put(
    "/{collection_id}/restore/{child_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def restore(
    user: Annotated[Auth.AuthorizedUser, Depends(Auth.authorized_user())],
    collection_id: int,
    child_id: int,
    sql_session: Annotated[SQL.AsyncSession, Depends(SQL.get_async_session)],
) -> None:
    parents: list[SQL.Tables.Parent] = (
        await sql_session.exec(
            SQL.select(SQL.Tables.Parent)
            .join(SQL.Tables.Parenthood)
            .where(SQL.Tables.Parenthood.child_id == child_id)
        )
    ).all()

    if user.user_id not in [parent.id for parent in parents]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to unsubscribe this child",
        )

    collection: SQL.Tables.Collection = (
        await sql_session.exec(
            SQL.select(SQL.Tables.Collection).where(
                SQL.Tables.Collection.id == collection_id
            )
        )
    ).first()

    if collection.status != CollectionStatus.OPEN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot restore from a collection with a status other than OPEN",
        )

    entry_to_delete = (
        await sql_session.exec(
            SQL.select(SQL.Tables.CollectionOperation).where(
                SQL.Tables.CollectionOperation.child_id == child_id,
                SQL.Tables.CollectionOperation.collection_id == collection_id,
                SQL.Tables.CollectionOperation.operation_type
                != CollectionOperationType.PAY,
            )
        )
    ).first()

    if not entry_to_delete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No operation to restore found",
        )

    try:
        await sql_session.delete(entry_to_delete)
        await sql_session.commit()
    except Exception:
        await sql_session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to restore child",
        )


@collection_router.put(
    "/{collection_id}/refund/{child_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def refund(
    user: Annotated[Auth.AuthorizedUser, Depends(Auth.authorized_user())],
    collection_id: int,
    child_id: int,
    sql_session: Annotated[SQL.AsyncSession, Depends(SQL.get_async_session)],
) -> None:
    parents: list[SQL.Tables.Parent] = (
        await sql_session.exec(
            SQL.select(SQL.Tables.Parent)
            .join(SQL.Tables.Parenthood)
            .where(SQL.Tables.Parenthood.child_id == child_id)
        )
    ).all()

    if user.user_id not in [parent.id for parent in parents]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to withdraw this child",
        )

    collection: SQL.Tables.Collection = (
        await sql_session.exec(
            SQL.select(SQL.Tables.Collection).where(
                SQL.Tables.Collection.id == collection_id
            )
        )
    ).first()

    if collection.status != CollectionStatus.OPEN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot withdraw from a collection with a status other than OPEN",
        )

    operation = (
        await sql_session.exec(
            SQL.select(SQL.Tables.CollectionOperation).where(
                SQL.Tables.CollectionOperation.child_id == child_id,
                SQL.Tables.CollectionOperation.collection_id == collection_id,
                SQL.Tables.CollectionOperation.operation_type
                == CollectionOperationType.PAY,
            )
        )
    ).first()

    if not operation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No operation to restore found",
        )

    collection_bank_account: SQL.Tables.BankAccount = (
        await sql_session.exec(
            SQL.select(SQL.Tables.BankAccount).where(
                SQL.Tables.BankAccount.id == collection.bank_account_id
            )
        )
    ).first()

    available_collection_funds = await collection_bank_account.get_balance(sql_session)

    if available_collection_funds < collection.price:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient funds in the collection account",
        )

    # Parent who is responsible for the child, might be different from the one who paid
    # Find the parent who paid for the child to refund to them
    parent: SQL.Tables.Parent = (
        await sql_session.exec(
            SQL.select(SQL.Tables.Parent).where(
                SQL.Tables.Parent.id == operation.requester_id
            )
        )
    ).first()

    if not parent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requestor not found. Cannot refund",
        )

    child: SQL.Tables.Child = (
        await sql_session.exec(
            SQL.select(SQL.Tables.Child).where(SQL.Tables.Child.id == child_id)
        )
    ).first()

    payment = SQL.Tables.BankAccountOperation(
        amount=collection.price,
        title=f"Collection refund - {collection.name}",
        description=f"Refund collection payment for child {child.name} {child.surname}",
        source_account_id=collection.bank_account_id,
        destination_account_id=parent.account_id,
    )

    try:
        sql_session.add(payment)
        await sql_session.commit()
        await sql_session.refresh(payment)
        operation.operation_type = CollectionOperationType.REFUND
        operation.operation_date = datetime.now()
        operation.requester_id = user.user_id
        operation.payment_id = payment.operation_id
        await sql_session.commit()
    except Exception:
        await sql_session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to restore child",
        )


@collection_router.delete("/{collection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    user: Annotated[Auth.AuthorizedUser, Depends(Auth.authorized_user(ADMIN_USER))],
    collection_id: int,
    sql_session: Annotated[SQL.AsyncSession, Depends(SQL.get_async_session)],
):
    try:
        await collection_service.delete(sql_session, collection_id)
    except Exception as e:
        logger.error(f"Error deleting collection ID {collection_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete collection",
        )


@collection_router.post(
    "/{collection_id}/cancel", status_code=status.HTTP_204_NO_CONTENT
)
async def cancel_collection(
    collection_id: int,
    user: Annotated[Auth.AuthorizedUser, Depends(Auth.authorized_user())],
    sql_session: Annotated[SQL.AsyncSession, Depends(SQL.get_async_session)],
):
    if not (
        collection := (
            await sql_session.exec(
                SQL.select(SQL.Tables.Collection).where(
                    SQL.Tables.Collection.id == collection_id
                )
            )
        ).first()
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found",
        )

    parent_profile = await parent_repository.get_by_user_account(
        sql_session, user.user_id
    )

    if parent_profile.account_id != collection.owner_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not the owner of this collection",
        )

    if collection.status != CollectionStatus.OPEN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel collection with a status other than OPEN",
        )

    payments_to_returns: list[SQL.Tables.CollectionOperation] = (
        await sql_session.exec(
            SQL.select(
                SQL.Tables.Child.id.label("child_id"),
                SQL.Tables.Child.name.label("child_name"),
                SQL.Tables.Child.surname.label("child_surname"),
                SQL.Tables.BankAccountOperation.source_account_id.label(
                    "source_account_id"
                ),
                SQL.Tables.BankAccountOperation.operation_date.label("operation_date"),
            )
            .select_from(SQL.Tables.CollectionOperation)
            .join(SQL.Tables.Child)
            .join(SQL.Tables.BankAccountOperation)
            .where(
                SQL.Tables.CollectionOperation.collection_id == collection_id,
                SQL.Tables.CollectionOperation.operation_type
                == CollectionOperationType.PAY,
            )
        )
    ).all()

    collection_bank_account: SQL.Tables.BankAccount = (
        await sql_session.exec(
            SQL.select(SQL.Tables.BankAccount).where(
                SQL.Tables.BankAccount.id == collection.bank_account_id
            )
        )
    ).first()

    available_collection_funds = await collection_bank_account.get_balance(sql_session)

    if available_collection_funds < collection.price * len(payments_to_returns):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient funds in the collection account to proceed cancellation",
        )

    child_status: list[SQL.Tables.CollectionOperation] = (
        await sql_session.exec(
            SQL.select(SQL.Tables.CollectionOperation).where(
                SQL.Tables.CollectionOperation.collection_id == collection_id
            )
        )
    ).all()

    # key is child_id, value is payment_id
    payment_id_helper: dict[int, int] = {}

    try:
        for payment in payments_to_returns:
            refund_payment = SQL.Tables.BankAccountOperation(
                amount=collection.price,
                title=f"Cancelled collection refund - {collection.name}",
                description=f"Cancelled collection refund for child {payment.child_name} {payment.child_surname}",
                source_account_id=collection.bank_account_id,
                destination_account_id=payment.source_account_id,
            )

            sql_session.add(refund_payment)
            await sql_session.commit()
            await sql_session.refresh(refund_payment)
            payment_id_helper[payment.child_id] = refund_payment.operation_id

        for i in range(len(child_status)):
            if refund_payment_id_to_set := payment_id_helper.get(
                child_status[i].child_id, None
            ):
                child_status[i].payment_id = refund_payment_id_to_set

            child_status[i].operation_type = CollectionOperationType.REFUND

        await sql_session.commit()
    except Exception:
        await sql_session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to process refund payment",
        )

    collection.status = CollectionStatus.CANCELLED

    try:
        await sql_session.commit()
    except Exception:
        await sql_session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not cancel collection",
        )

    collection_money_after_refunds = await collection_bank_account.get_balance(
        sql_session
    )

    if collection_money_after_refunds > 0:
        collection_bank_account_operation = BankAccountOperation(
            amount=collection_money_after_refunds,
            title=f"Cancelled collection refund - {collection.name}",
            description="Refund cashier deposits",
            source_account_id=collection.bank_account_id,
            destination_account_id=parent_profile.bank_account_id,
        )

        try:
            sql_session.add(collection_bank_account_operation)
            await sql_session.commit()
        except Exception:
            await sql_session.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to process refund payment",
            )


@collection_router.put("/{collection_id}/block", status_code=status.HTTP_204_NO_CONTENT)
async def block_collection(
    collection_id: int,
    user: Annotated[Auth.AuthorizedUser, Depends(Auth.authorized_user(ADMIN_USER))],
    sql_session: Annotated[SQL.AsyncSession, Depends(SQL.get_async_session)],
):
    collection: SQL.Tables.Collection = (
        await sql_session.exec(
            SQL.select(SQL.Tables.Collection).where(
                SQL.Tables.Collection.id == collection_id
            )
        )
    ).first()

    if collection.status != CollectionStatus.OPEN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot block a collection with a status other than OPEN",
        )

    collection.status = CollectionStatus.BLOCKED

    try:
        await sql_session.commit()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not block collection",
        )


@collection_router.put(
    "/{collection_id}/unblock", status_code=status.HTTP_204_NO_CONTENT
)
async def unblock_collection(
    collection_id: int,
    user: Annotated[Auth.AuthorizedUser, Depends(Auth.authorized_user(ADMIN_USER))],
    sql_session: Annotated[SQL.AsyncSession, Depends(SQL.get_async_session)],
):
    collection: SQL.Tables.Collection = (
        await sql_session.exec(
            SQL.select(SQL.Tables.Collection).where(
                SQL.Tables.Collection.id == collection_id
            )
        )
    ).first()

    if collection.status != CollectionStatus.BLOCKED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot unblock a collection with a status other than BLOCKED",
        )

    collection.status = CollectionStatus.OPEN

    try:
        await sql_session.commit()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not unblock collection",
        )
