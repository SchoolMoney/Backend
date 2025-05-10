from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
import datetime
import src.SQL as SQL
from src.SQL.Enum.Privilege import ADMIN_USER
from src.SQL.Tables import BankAccountOperation
from src.Service import Auth
from src.repository import bank_account_repository
from src.repository import parent_repository
from src.Model.BankAccount import BankAccount, ExternalBankAccountOperation
from src.Model.BankAccountOperation import BankAccountBalance
from src.repository.bank_account_repository import get_bank_account_operations_with_iban
from src.repository.parent_repository import get_by_user_account
import src.SQL.Enum.CollectionStatus as CollectionStatus
from src.Model.BankAccountOperation import (
    BankAccountOperation as ModelBankAccountOperation,
)

bank_account_router = APIRouter()


@bank_account_router.get(
    "/user", status_code=status.HTTP_200_OK, response_model=BankAccount
)
async def get_bank_account_for_auth_user(
    user: Annotated[Auth.AuthorizedUser, Depends(Auth.authorized_user())],
    sql_session: Annotated[SQL.AsyncSession, Depends(SQL.get_async_session)],
) -> BankAccount:
    parent_profile = await parent_repository.get_by_user_account(
        sql_session, user.user_id
    )

    sql_bank_account = (
        await sql_session.exec(
            SQL.select(SQL.Tables.BankAccount).where(
                SQL.Tables.BankAccount.id == parent_profile.bank_account_id
            )
        )
    ).first()

    return BankAccount(
        **{
            **sql_bank_account.model_dump(),
            "balance": await sql_bank_account.get_balance(sql_session),
        }
    )


@bank_account_router.post(
    "/user/deposit", status_code=status.HTTP_200_OK, response_model=BankAccountBalance
)
async def deposit(
    user: Annotated[Auth.AuthorizedUser, Depends(Auth.authorized_user())],
    sql_session: Annotated[SQL.AsyncSession, Depends(SQL.get_async_session)],
    requestData: ExternalBankAccountOperation,
):
    parent_profile = await parent_repository.get_by_user_account(
        sql_session, user.user_id
    )
    if not (
        sql_bank_account := (
            await sql_session.exec(
                SQL.select(SQL.Tables.BankAccount).where(
                    SQL.Tables.BankAccount.id == parent_profile.bank_account_id
                )
            )
        ).first()
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bank account not found",
        )

    try:
        sql_session.add(
            SQL.Tables.BankAccountOperation(
                operation_date=datetime.date.today(),
                amount=requestData.amount,
                title="Money deposit",
                description="Money deposit",
                source_account_id=None,
                destination_account_id=sql_bank_account.id,
            )
        )
        await sql_session.commit()
    except Exception:
        await sql_session.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not deposit money",
        )

    balance = await sql_bank_account.get_balance(sql_session)

    return BankAccountBalance(
        account_id=sql_bank_account.id,
        balance=balance,
    )


@bank_account_router.post(
    "/user/withdraw", status_code=status.HTTP_200_OK, response_model=BankAccountBalance
)
async def withdraw(
    user: Annotated[Auth.AuthorizedUser, Depends(Auth.authorized_user())],
    sql_session: Annotated[SQL.AsyncSession, Depends(SQL.get_async_session)],
    requestData: ExternalBankAccountOperation,
):
    parent_profile = await parent_repository.get_by_user_account(
        sql_session, user.user_id
    )
    if not (
        sql_bank_account := (
            await sql_session.exec(
                SQL.select(SQL.Tables.BankAccount).where(
                    SQL.Tables.BankAccount.id == parent_profile.bank_account_id
                )
            )
        ).first()
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bank account not found",
        )

    available_balance = await sql_bank_account.get_balance(sql_session)

    if available_balance < requestData.amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not enough money",
        )

    try:
        sql_session.add(
            SQL.Tables.BankAccountOperation(
                operation_date=datetime.date.today(),
                amount=requestData.amount,
                title="Money Withdrawal",
                description=f"Money Withdrawal to {requestData.account_number}",
                source_account_id=sql_bank_account.id,
                destination_account_id=None,
            )
        )
        await sql_session.commit()
    except Exception:
        await sql_session.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not withdraw money",
        )

    balance = await sql_bank_account.get_balance(sql_session)

    return BankAccountBalance(
        account_id=sql_bank_account.id,
        balance=balance,
    )


@bank_account_router.get(
    "/{bank_account_id}",
    status_code=status.HTTP_200_OK,
    response_model=SQL.Tables.BankAccount,
)
async def get(
    user: Annotated[Auth.AuthorizedUser, Depends(Auth.authorized_user())],
    bank_account_id: int,
    sql_session: Annotated[SQL.AsyncSession, Depends(SQL.get_async_session)],
) -> SQL.Tables.BankAccount:
    try:
        return await bank_account_repository.get_by_id(sql_session, bank_account_id)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve bank account",
        )


@bank_account_router.get(
    "/operations/{bank_account_id}",
    status_code=status.HTTP_200_OK,
    response_model=list[ModelBankAccountOperation],
)
async def get_bank_account_operations_by_id(
    bank_account_id: int,
    user: Annotated[Auth.AuthorizedUser, Depends(Auth.authorized_user())],
    sql_session: Annotated[SQL.AsyncSession, Depends(SQL.get_async_session)],
):
    requester_parent_account = await get_by_user_account(sql_session, user.user_id)

    if (
        requester_parent_account.bank_account_id != bank_account_id
        and user.user_privilege != ADMIN_USER
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bank account cannot be viewed by this person",
        )

    operations = await get_bank_account_operations_with_iban(
        sql_session,
        bank_account_id,
    )
    if not operations:
        raise HTTPException(
            status_code=status.HTTP_204_NO_CONTENT,
        )
    return operations


@bank_account_router.post(
    "/{bank_account_id}/collection/withdraw",
    status_code=status.HTTP_200_OK,
    response_model=BankAccountBalance,
)
async def withdraw_from_collection(
    bank_account_id: int,
    requestData: ExternalBankAccountOperation,
    user: Annotated[Auth.AuthorizedUser, Depends(Auth.authorized_user())],
    sql_session: Annotated[SQL.AsyncSession, Depends(SQL.get_async_session)],
):
    sql_bank_account = (
        await sql_session.exec(
            SQL.select(SQL.Tables.BankAccount).where(
                SQL.Tables.BankAccount.id == bank_account_id
            )
        )
    ).first()

    collection = (
        await sql_session.exec(
            SQL.select(SQL.Tables.Collection).where(
                SQL.Tables.Collection.bank_account_id == bank_account_id
            )
        )
    ).first()

    parent_profile = await parent_repository.get_by_user_account(
        sql_session, user.user_id
    )

    if parent_profile.account_id != collection.owner_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not the owner of this collection",
        )

    available_balance = await sql_bank_account.get_balance(sql_session)

    if collection.status == CollectionStatus.BLOCKED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot withdraw money from blocked collection",
        )

    if available_balance < requestData.amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not enough money",
        )

    try:
        sql_session.add(
            SQL.Tables.BankAccountOperation(
                operation_date=datetime.date.today(),
                amount=requestData.amount,
                title="Money Withdrawal",
                description=f"Money Withdrawal to {requestData.account_number}",
                source_account_id=sql_bank_account.id,
                destination_account_id=None,
            )
        )
        collection.withdrawn_money += requestData.amount
        await sql_session.commit()
    except Exception:
        await sql_session.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not withdraw money",
        )

    balance = await sql_bank_account.get_balance(sql_session)

    return BankAccountBalance(
        account_id=sql_bank_account.id,
        balance=balance,
    )
