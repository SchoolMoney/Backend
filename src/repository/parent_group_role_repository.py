from typing import Optional
from sqlmodel import col, select

import src.SQL as SQL
from src.SQL.Tables import ParentGroupRole
import src.SQL.Enum.ParentRole as ParentRole


async def get(session: SQL.AsyncSession, class_group_id: int, parent_id: int) -> Optional[ParentGroupRole]:
    query = select(ParentGroupRole).where(
        ParentGroupRole.class_group_id == class_group_id,
        ParentGroupRole.parent_id == parent_id
    )
    
    result = await session.exec(query)
    return result.first()


async def get_cashier(session: SQL.AsyncSession, class_group_id: int) -> Optional[ParentGroupRole]:
    query = select(ParentGroupRole).where(
        ParentGroupRole.class_group_id == class_group_id,
        ParentGroupRole.role == ParentRole.CASHIER
    )
    
    result = await session.exec(query)
    return result.first()
  

async def create(session: SQL.AsyncSession, data: ParentGroupRole) -> ParentGroupRole:
    try:
        session.add(data)
        await session.commit()
        await session.refresh(data)
        return data
    except Exception as e:
        await session.rollback()
        raise e

