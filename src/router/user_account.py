from typing import Annotated
from fastapi import APIRouter, Depends, status
from src.Model.UserAccount import RegisterUser
import src.SQL as SQL

user_router = APIRouter()


@user_router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(
    sql_session: Annotated[SQL.AsyncSession, Depends(SQL.get_async_session)],
    user: RegisterUser,
) -> None:
    user_account = SQL.Tables.UserAccount(**user.model_dump())
    sql_session.add(user_account)
    await sql_session.commit()
