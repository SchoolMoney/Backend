from sqlmodel import select

from src import SQL as SQL
from src.SQL.Tables import UserAccount, Parent, ParentGroupRole, ClassGroup, Collection


async def check_if_user_can_view_collection(session: SQL.AsyncSession, collection_id: int, user_id: int) -> bool:
    query = select(UserAccount.id).select_from(UserAccount).join(
        Parent, UserAccount.id == Parent.account_id
    ).join(
        ParentGroupRole, Parent.id == ParentGroupRole.parent_id
    ).join(
        ClassGroup, ParentGroupRole.class_group_id == ClassGroup.id
    ).join(
        Collection, Collection.class_group_id == ClassGroup.id
    ).where(
        UserAccount.id == user_id,
        Collection.id == collection_id
    )

    result = (await session.exec(query)).first()
    return result is not None
