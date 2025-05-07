from typing import List, Optional, Sequence
from sqlmodel import col, select

from src.SQL.Tables.People import Parenthood
import src.SQL as SQL
from src.SQL.Tables import Child


async def get_by_child_id(
    session: SQL.AsyncSession, child_id: int
) -> Optional[Parenthood]:
    query = select(Parenthood).where(Parenthood.child_id == child_id)
    result = await session.exec(query)

    return result.first()


async def create(session: SQL.AsyncSession, parenthood: Parenthood) -> Parenthood:
    """Creates a relationship between child & parent"""
    try:
        session.add(parenthood)
        await session.commit()
        await session.refresh(parenthood)
        return parenthood
    except Exception as e:
        await session.rollback()
        raise e


async def delete_by_child_id(session: SQL.AsyncSession, child_id: int):
    try:
        db_parenthood = await get_by_child_id(session, child_id)
        if db_parenthood is None:
            return

        session.delete(db_parenthood)
        await session.commit()
    except Exception as e:
        await session.rollback()
        raise e
