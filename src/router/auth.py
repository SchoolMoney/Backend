from typing import Annotated
from fastapi import APIRouter, Depends, status
import src.SQL as SQL
import src.Service.Auth as Auth
import src.Model.UserAccount as UserModel

auth_router = APIRouter()


@auth_router.post("/login", response_model=Auth.Token)
async def login(
    form_data: UserModel.Login,
    sql_session: Annotated[SQL.AsyncSession, Depends(SQL.async_session_generator)],
) -> Auth.Token:
    return await Auth.user_login(form_data, sql_session)


@auth_router.post("/refresh", response_model=Auth.Token)
async def refresh_token(
    refresh_token: str,
    sql_session: Annotated[SQL.AsyncSession, Depends(SQL.async_session_generator)],
) -> Auth.Token:
    return await Auth.refresh_token(refresh_token, sql_session)


@auth_router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    user: Annotated[Auth.AuthorizedUser, Depends(Auth.authorized_user())],
):
    Auth.user_logout(user)
