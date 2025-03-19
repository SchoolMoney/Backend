from typing import Annotated
from fastapi import APIRouter, Depends, status
from src.Model.UserAccount import RegisterUser, User
import src.SQL as SQL
import src.Service.Auth as Auth

user_router = APIRouter()


@user_router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(
    sql_session: Annotated[SQL.AsyncSession, Depends(SQL.get_async_session)],
    user: RegisterUser,
) -> None:
    user_account = SQL.Tables.UserAccount(**user.model_dump())
    sql_session.add(user_account)
    await sql_session.commit()


@user_router.get("/me", response_model=User)
async def me(
    user: Annotated[Auth.AuthorizedUser, Depends(Auth.authorized_user())],
    sql_session: Annotated[SQL.AsyncSession, Depends(SQL.get_async_session)],
) -> SQL.Tables.UserAccount:
    """
    Returns information about logged in user.
    """
    return (
        await sql_session.exec(
            SQL.select(SQL.Tables.UserAccount).filter(
                SQL.Tables.UserAccount.id == user.user_id
            )
        )
    ).first()
