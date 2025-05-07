from http.client import HTTPException
from typing import Optional

from fastapi import status
from src.Model.BankAccount import BankAccount
from src.Service.IBAN_generator.IBAN_gen import generate_iban
import src.SQL as SQL


async def create_bank_account(
    session: SQL.AsyncSession,
) -> SQL.Tables.Financial.BankAccount:
    insert_success = False
    while not insert_success:
        try:
            iban_number = generate_iban()
        except Exception as e:
            raise HTTPException(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        bank_account_record = SQL.Tables.Financial.BankAccount(
            account_number=iban_number,
        )

        session.add(bank_account_record)
        try:
            await session.commit()
            insert_success = True
        except Exception as e:
            if e.orig.pgcode == "23505":
                await session.rollback()
                insert_success = False
            else:
                raise e
        return bank_account_record


async def update_bank_account(
    account_id: id, bank_account: BankAccount
) -> SQL.Tables.Financial.BankAccount:
    session = await SQL.get_async_session()

    if (
        modified_record := (
            await session.exec(
                SQL.select(SQL.Tables.Financial.BankAccount).filter(
                    SQL.Tables.Financial.BankAccount.id == account_id
                )
            )
        ).first()
    ) is None:
        raise HTTPException(status=status.HTTP_400_BAD_REQUEST, detail="No account")

    for field in bank_account.model_dump():
        setattr(modified_record, field, getattr(bank_account, field))

    try:
        await session.commit()
    except Exception as e:
        raise e

    await session.refresh(modified_record)
    await session.close()
    return modified_record


async def get_account_by_id(
    account_id: id,
) -> Optional[SQL.Tables.Financial.BankAccount]:
    session = await SQL.get_async_session()
    if (
        parent_record := (
            await session.exec(
                SQL.select(SQL.Tables.Financial.BankAccount).filter(
                    SQL.Tables.Financial.BankAccount.id == account_id
                )
            )
        ).first()
    ) is None:
        raise HTTPException(status=status.HTTP_204_NO_CONTENT, detail="No account")
    await session.close()
    return parent_record


async def delete_bank_account(
    account_id: id,
) -> Optional[SQL.Tables.Financial.BankAccount]:
    session = await SQL.get_async_session()
    try:
        account_data = await get_account_by_id(account_id)
        if not account_data:
            return None

        await session.delete(account_data)
        await session.commit()
        await session.close()
        return account_data
    except Exception as e:
        await session.rollback()
        session.close()
        raise e
