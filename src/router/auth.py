from typing import Annotated
from fastapi import APIRouter, Depends, status
import src.SQL as SQL
import src.Service.Auth as Auth
from src.Model.UserAccount import User

auth_router = APIRouter()


@auth_router.post("/login", response_model=Auth.Token)
async def login(
    form_data: Auth.Login,
    sql_session: Annotated[SQL.AsyncSession, Depends(SQL.get_async_session)],
) -> Auth.Token:
    return await Auth.user_login(form_data, sql_session)


@auth_router.post("/refresh", response_model=Auth.Token)
async def refresh_token(
    refresh_token: str,
    sql_session: Annotated[SQL.AsyncSession, Depends(SQL.get_async_session)],
) -> Auth.Token:
    return await Auth.refresh_token(refresh_token, sql_session)


@auth_router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    user: Annotated[Auth.AuthorizedUser, Depends(Auth.authorized_user())],
):
    Auth.user_logout(user)


@auth_router.get("/me", response_model=User)
async def me(
    user: Annotated[Auth.AuthorizedUser, Depends(Auth.authorized_user())],
    sql_session: Annotated[SQL.AsyncSession, Depends(SQL.get_async_session)],
) -> SQL.Tables.UserAccount:
    return (
        await sql_session.exec(
            SQL.select(SQL.Tables.UserAccount).filter(
                SQL.Tables.UserAccount.id == user.user_id
            )
        )
    ).first()
