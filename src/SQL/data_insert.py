from src.config import DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_PASSWORD
from src.Model.UserAccount import RegisterUser
from .connection import get_async_session
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from .Enum import AccountStatus, Privilege
from .Tables.People import UserAccount


async def insert_data() -> None:
    """
    Insert default data into database.
    """
    session: AsyncSession = await get_async_session()
    await insert_users(session)


async def insert_users(session: AsyncSession) -> None:
    users = [
        UserAccount(
            **{
                **RegisterUser(
                    username=DEFAULT_ADMIN_USERNAME,
                    password=DEFAULT_ADMIN_PASSWORD,
                ).model_dump(),
                "status": AccountStatus.ENABLED,
                "privilege": Privilege.ADMIN_USER,
            }
        )
    ]

    for user in users:
        if (
            existing_account := (
                await session.exec(
                    select(UserAccount).filter(UserAccount.username == user.username)
                )
            ).first()
        ) is not None:
            await session.delete(existing_account)
            await session.commit()
        session.add(user)
        await session.commit()
