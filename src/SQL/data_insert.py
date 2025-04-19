from typing import List

from src.config import DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_PASSWORD
from src.Model.UserAccount import RegisterUser
from .connection import get_async_session
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from .Enum import AccountStatus, Privilege
from .Tables.People import UserAccount, Parent
from ..Model.PeopleModel import ParentModel
from ..Service.IBAN_generator.iban_db_service import create_bank_account


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
            parent = (await session.exec(select(Parent).filter(Parent.name == DEFAULT_ADMIN_USERNAME,
                                                     Parent.surname == DEFAULT_ADMIN_USERNAME))).first()
            await session.delete(parent)
            await session.delete(existing_account)
            await session.commit()
        session.add(user)
        await session.commit()

    await create_parent_for_user(session, users)

async def create_parent_for_user(session: AsyncSession, users: List[UserAccount]) -> None:
    parent: ParentModel = ParentModel(
            **{
                "name": DEFAULT_ADMIN_USERNAME,
                "surname": DEFAULT_ADMIN_USERNAME,
                "phone":"000000000",
                "city": DEFAULT_ADMIN_USERNAME,
                "street": DEFAULT_ADMIN_USERNAME,
                "house_number": '0'
            }
        )

    for user in users:
        account_record_id = await session.exec(select(UserAccount.id).filter(UserAccount.username == user.username))
        account_record_id = account_record_id.first()

        bank_account = await create_bank_account(session)
        parent_record = Parent(
            **{
                **parent.model_dump(),
                "bank_account_id": bank_account.id,
                "account_id": account_record_id
            }
        )
        session.add(parent_record)
        await session.commit()

