from typing import Annotated
from fastapi import APIRouter, Depends, status, HTTPException
from src.Model.UserAccount import RegisterUser, User
import src.SQL as SQL
import src.Service.Auth as Auth

user_router = APIRouter()


@user_router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(
    sql_session: Annotated[SQL.AsyncSession, Depends(SQL.async_session_generator)],
    user: RegisterUser,
) -> None:
    user_account = SQL.Tables.UserAccount(**user.model_dump())
    sql_session.add(user_account)
    try:
        await sql_session.commit()
    except Exception as e:
        if e.orig.pgcode == "23505":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already exists",
            )


@user_router.get("/me", response_model=User)
async def me(
    user: Annotated[Auth.AuthorizedUser, Depends(Auth.authorized_user())],
    sql_session: Annotated[SQL.AsyncSession, Depends(SQL.async_session_generator)],
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
