from typing import Annotated
from fastapi import APIRouter, Depends, status, HTTPException
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


@auth_router.put("/password", status_code=status.HTTP_204_NO_CONTENT)
async def update_password(
    request: UserModel.ChangePassword,
    user: Annotated[Auth.AuthorizedUser, Depends(Auth.authorized_user())],
    sql_session: Annotated[SQL.AsyncSession, Depends(SQL.async_session_generator)],
):
    if request.new_password == request.old_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password cannot be the same as old password",
        )

    DB_user: SQL.Tables.UserAccount = (
        await sql_session.exec(
            SQL.select(SQL.Tables.UserAccount).filter(
                SQL.Tables.UserAccount.id == user.user_id
            )
        )
    ).first()

    if DB_user.password != request.old_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User is unauthorized"
        )

    DB_user.password = request.new_password
    await sql_session.commit()


@auth_router.put("/identity", status_code=status.HTTP_204_NO_CONTENT)
async def update_identity(
    request: UserModel.UpdateIdentity,
    user: Annotated[Auth.AuthorizedUser, Depends(Auth.authorized_user())],
    sql_session: Annotated[SQL.AsyncSession, Depends(SQL.async_session_generator)],
):
    DB_user: SQL.Tables.UserAccount = (
        await sql_session.exec(
            SQL.select(SQL.Tables.UserAccount).filter(
                SQL.Tables.UserAccount.id == user.user_id
            )
        )
    ).first()

    DB_user.username = request.username
    await sql_session.commit()
