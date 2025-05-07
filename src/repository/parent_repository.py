from typing import Optional, List
from sqlmodel import Sequence, col, select

import src.SQL as SQL
from src.Model.ParentBasicInfo import ParentBasicInfo
from src.SQL.Tables import Parent


async def get_by_user_account(
    session: SQL.AsyncSession, account_id: int
) -> Optional[Parent]:
    query = select(Parent).where(Parent.account_id == account_id)

    result = await session.exec(query)
    return result.first()


async def get_all(session: SQL.AsyncSession) -> Sequence[Parent]:
    query = select(Parent)

    result = await session.exec(query)
    return result.all()


async def get_all_basic_info(session: SQL.AsyncSession) -> List[ParentBasicInfo]:
    query = select(Parent.id, Parent.name, Parent.surname)

    result = await session.exec(query)
    parents_data = result.all()

    return [
        ParentBasicInfo(
            id=int(parent_id),
            first_name=str(parent_name),
            last_name=str(parent_surname),
        )
        for parent_id, parent_name, parent_surname in parents_data
    ]


async def get_by_id(session: SQL.AsyncSession, parent_id: int) -> Optional[Parent]:
    query = select(Parent).where(Parent.id == parent_id)

    result = await session.exec(query)
    return result.first()


async def update_by_user(
    session: SQL.AsyncSession, updated_profile: Parent, account_id: int
):
    try:
        user_parent_profile = await get_by_user_account(session, account_id)

        update_data = updated_profile.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(user_parent_profile, key, value)

        session.add(user_parent_profile)
        await session.commit()
        await session.refresh(user_parent_profile)
    except Exception as e:
        await session.rollback()
        raise e
