from typing import List, Optional, Sequence
from sqlmodel import col, select

from src.SQL.Tables.People import Parenthood
import src.SQL as SQL
from src.SQL.Tables import Child


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