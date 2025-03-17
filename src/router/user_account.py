from typing import Annotated
from fastapi import APIRouter, Depends

import src.SQL as SQL

user_router = APIRouter()


@user_router.get("/create_user", response_model=list[SQL.Tables.UserAccount])
async def get_users(
    sql_session: Annotated[SQL.AsyncSession, Depends(SQL.get_async_session)],
) -> list[SQL.Tables.UserAccount]:
    return (await sql_session.exec(SQL.select(SQL.Tables.UserAccount))).all()
