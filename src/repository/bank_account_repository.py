from sqlmodel import or_
from typing import Optional, Sequence
from sqlmodel import col, select

import src.SQL as SQL
from src.SQL.Tables import BankAccount, BankAccountOperation


async def get_by_id(
    session: SQL.AsyncSession, BankAccount_id: int
) -> Optional[BankAccount]:
    query = select(BankAccount).where(BankAccount.id == BankAccount_id)
    result = await session.exec(query)

    return result.first()


async def get_all(session: SQL.AsyncSession) -> Sequence[BankAccount]:
    query = select(BankAccount)
    result = await session.exec(query)

    return result.all()

async def get_bank_account_operations(session: SQL.AsyncSession, bank_account_id) -> Optional[Sequence[BankAccountOperation]]:
    query = select(BankAccountOperation).where(
        or_(
            BankAccountOperation.source_account_id == bank_account_id,
            BankAccountOperation.destination_account_id == bank_account_id
        )
    )

    result = (await session.exec(query)).all()
    if not result:
        return None

    return result
