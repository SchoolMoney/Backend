import src.SQL as SQL

import src.SQL.Enum.AccountStatus as AccountStatus


async def get_user_account(
    sql_session: SQL.AsyncSession, user_id: int = None, username: str = None
) -> SQL.Tables.UserAccount:
    filters = []

    if user_id:
        filters.append(SQL.Tables.UserAccount.id == user_id)

    if username:
        filters.append(SQL.Tables.UserAccount.username == username)

    user: SQL.Tables.UserAccount = (
        await sql_session.exec(SQL.select(SQL.Tables.UserAccount).filter(*filters))
    ).first()

    if user is None or user.status != AccountStatus.ENABLED:
        return None
    return user
