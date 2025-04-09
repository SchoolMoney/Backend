from typing import Annotated, List, Optional, Sequence
from fastapi import APIRouter, Depends, HTTPException, Query, status

import src.SQL as SQL
from src.SQL.Tables import BankAccount
from src.Service import Auth
from src.repository import bank_account_repository

bank_account_router = APIRouter()


@bank_account_router.get("/{bank_account_id}", status_code=status.HTTP_200_OK, response_model=BankAccount)
async def get(
    user: Annotated[Auth.AuthorizedUser, Depends(Auth.authorized_user())],
    bank_account_id: int,
    sql_session: Annotated[SQL.AsyncSession, Depends(SQL.get_async_session)],
) -> BankAccount:
    try:
        return await bank_account_repository.get_by_id(sql_session, bank_account_id)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve bank account"
        )