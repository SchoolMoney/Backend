from typing import Optional
from sqlmodel import col, select

import src.SQL as SQL
from src.SQL.Tables import ParentGroupRole


async def get(session: SQL.AsyncSession, class_group_id: int, parent_id: int) -> Optional[ParentGroupRole]:
    query = select(ParentGroupRole).where(
        ParentGroupRole.class_group_id == class_group_id,
        ParentGroupRole.parent_id == parent_id
    )
    
    result = await session.exec(query)
    return result.first()
