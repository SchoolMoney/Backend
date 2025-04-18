from typing import Annotated
from fastapi import APIRouter, Depends, status, HTTPException
from src.Model.UserAccount import RegisterUser, UpdateUserAccountStatus, User, UpdateUserAccountPrivilege
import src.SQL as SQL
import src.Service.Auth as Auth
from src.SQL.Enum.Privilege import ADMIN_USER
from src.repository import parent_repository, account_repository

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


@user_router.get('/parent/{parent_id}', response_model=User)
async def get_user_by_parent(
    user: Annotated[Auth.AuthorizedUser, Depends(Auth.authorized_user(ADMIN_USER))],
    parent_id: int,
    sql_session: Annotated[SQL.AsyncSession, Depends(SQL.async_session_generator)],
) -> SQL.Tables.UserAccount:
    """
    Returns information about user by parent ID.
    """
    user_parent_profile = await parent_repository.get_by_id(sql_session, parent_id)
    return await account_repository.get_by_user(sql_session, user_parent_profile.account_id)


@user_router.put('/parent/{parent_id}')
async def update_user_parent_status(
    user: Annotated[Auth.AuthorizedUser, Depends(Auth.authorized_user(ADMIN_USER))],
    parent_id: int,
    request: UpdateUserAccountStatus,
    sql_session: Annotated[SQL.AsyncSession, Depends(SQL.async_session_generator)],
):
    user_parent_profile = await parent_repository.get_by_id(sql_session, parent_id)
    user = await account_repository.get_by_user(sql_session, user_parent_profile.account_id)
    user.status = request.status
    await sql_session.commit()

@user_router.put('/parent/privilege/{parent_id}')
async def update_user_parent_privilege(
    user: Annotated[Auth.AuthorizedUser, Depends(Auth.authorized_user(ADMIN_USER))],
    parent_id: int,
    request: UpdateUserAccountPrivilege,
    sql_session: Annotated[SQL.AsyncSession, Depends(SQL.async_session_generator)],
):
    user_parent_profile = await parent_repository.get_by_id(sql_session, parent_id)
    if user_parent_profile.account_id == user.user_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You cannot change your own privilege",
        )
    user = await account_repository.get_by_user(sql_session, user_parent_profile.account_id)
    user.privilege = request.privilege
    await sql_session.commit()

