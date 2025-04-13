from typing import Optional
from sqlmodel import Sequence, col, select

import src.SQL as SQL
from src.SQL.Tables import Parent


async def get_by_user_account(session: SQL.AsyncSession, account_id: int) -> Optional[Parent]:
    query = select(Parent).where(Parent.account_id == account_id)
    
    result = await session.exec(query)
    return result.first()
  

async def get_all(session: SQL.AsyncSession) -> Sequence[Parent]:
    query = select(Parent)
    
    result = await session.exec(query)
    return result.all()
