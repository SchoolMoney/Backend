from typing import Optional
from sqlmodel import col, select

import src.SQL as SQL
from src.SQL.Tables import UserAccount


async def get_by_user(session: SQL.AsyncSession, user_id: int) -> Optional[UserAccount]:
    query = select(UserAccount).where(UserAccount.id == user_id)
    
    result = await session.exec(query)
    return result.first()
