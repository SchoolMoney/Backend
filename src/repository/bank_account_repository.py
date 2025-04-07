from typing import Optional, Sequence
from sqlmodel import col, select

import src.SQL as SQL
from src.SQL.Tables import BankAccount


async def get_by_id(session: SQL.AsyncSession, BankAccount_id: int) -> Optional[BankAccount]:
    query = select(BankAccount).where(BankAccount.id == BankAccount_id)
    result = await session.exec(query)
    
    return result.first()
