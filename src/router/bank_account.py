from typing import Annotated, List, Optional, Sequence
from fastapi import APIRouter, Depends, HTTPException, Query, status
import datetime
import src.SQL as SQL
from src.Service import Auth
from src.repository import bank_account_repository
from src.repository import parent_repository
from src.Model.BankAccount import BankAccount, ExternalBankAccountOperation

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
                SQL.Tables.BankAccount.id == parent_profile.account_id
            )
        )
    ).first()

    return BankAccount(
        **{
            **sql_bank_account.model_dump(),
            "balance": await sql_bank_account.get_balance(sql_session),
        }
    )


@bank_account_router.post("/user/deposit", status_code=status.HTTP_204_NO_CONTENT)
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
                    SQL.Tables.BankAccount.id == parent_profile.account_id
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


@bank_account_router.post("/user/withdraw", status_code=status.HTTP_204_NO_CONTENT)
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
                    SQL.Tables.BankAccount.id == parent_profile.account_id
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
                title="Money Withdrawal",
                description="Money Withdrawal",
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
