from sqlmodel import or_
from typing import Optional, Sequence
from sqlmodel import select, func

import src.SQL as SQL
from src.SQL.Tables import BankAccount, BankAccountOperation
from src.Model.BankAccountOperation import (
    BankAccountOperation as ModelBankAccountOperation,
)


async def get_by_id(
    session: SQL.AsyncSession, BankAccount_id: int
) -> Optional[BankAccount]:
    query = select(BankAccount).where(BankAccount.id == BankAccount_id)
    result = await session.exec(query)

    return result.first()


async def get_all(session: SQL.AsyncSession) -> Sequence[BankAccount]:
    query = select(BankAccount)
    result = await session.exec(query)

    return result.all()


async def get_bank_account_operations(
    session: SQL.AsyncSession, bank_account_id
) -> Optional[Sequence[BankAccountOperation]]:
    query = select(BankAccountOperation).where(
        or_(
            BankAccountOperation.source_account_id == bank_account_id,
            BankAccountOperation.destination_account_id == bank_account_id,
        )
    )
    result = (await session.exec(query)).all()
    if not result:
        return None

    return result


async def get_bank_account_operations_with_iban(
    session: SQL.AsyncSession, bank_account_id
) -> list[ModelBankAccountOperation] | None:
    SourceAccount = SQL.aliased(BankAccount)
    DestinationAccount = SQL.aliased(BankAccount)

    query = (
        select(
            BankAccountOperation.operation_id.label("operation_id"),
            BankAccountOperation.operation_date.label("operation_date"),
            BankAccountOperation.amount.label("amount"),
            BankAccountOperation.title.label("title"),
            BankAccountOperation.description.label("description"),
            BankAccountOperation.source_account_id.label("source_account_id"),
            BankAccountOperation.destination_account_id.label("destination_account_id"),
            SourceAccount.account_number.label("source_iban"),
            DestinationAccount.account_number.label("destination_iban"),
        )
        .select_from(BankAccountOperation)
        .join(
            SourceAccount,
            BankAccountOperation.source_account_id == SourceAccount.id,
            isouter=True,
        )
        .join(
            DestinationAccount,
            BankAccountOperation.destination_account_id == DestinationAccount.id,
            isouter=True,
        )
        .where(
            or_(
                BankAccountOperation.source_account_id == bank_account_id,
                BankAccountOperation.destination_account_id == bank_account_id,
            )
        )
    )

    if not (result := (await session.exec(query)).all()):
        return None

    return result


async def get_bank_account_details(
    session: SQL.AsyncSession,
    bank_account_id: int,
    cashier_id: int | None = None,
) -> dict[str, str | int] | None:
    query = select(SQL.Tables.BankAccount).where(
        SQL.Tables.BankAccount.id == bank_account_id
    )
    detailed_info = {}

    result = (await session.exec(query)).first()

    detailed_info["balance"] = await result.get_balance(session)

    if cashier_id:
        cashier = (
            await session.exec(
                select(SQL.Tables.Parent).where(SQL.Tables.Parent.id == cashier_id)
            )
        ).first()

        withdrawn_money = (
            await session.exec(
                select(func.sum(BankAccountOperation.amount)).where(
                    BankAccountOperation.source_account_id == bank_account_id,
                    or_(
                        BankAccountOperation.destination_account_id
                        == cashier.bank_account_id,
                        BankAccountOperation.destination_account_id is None,
                    ),
                )
            )
        ).first()

        detailed_info["withdrawn_money"] = withdrawn_money or 0.0

    return {
        **result.model_dump(),
        **detailed_info,
    }
