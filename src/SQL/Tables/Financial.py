from sqlmodel import SQLModel, Field, select, func
from sqlmodel.ext.asyncio.session import AsyncSession
from datetime import datetime


class BankAccount(SQLModel, table=True):
    """
    Represents bank account of the collection or parent.
    """

    __tablename__ = "bank_account"
    id: int = Field(primary_key=True)
    account_number: str = Field(unique=True, min_length=26, max_length=26)
    is_locked: bool = Field(default=False)

    async def get_balance(self, session: AsyncSession) -> float:
        incoming_query = select(func.sum(BankAccountOperation.amount)).filter(
            BankAccountOperation.destination_account_id == self.id
        )
        outgoing_query = select(func.sum(BankAccountOperation.amount)).filter(
            BankAccountOperation.source_account_id == self.id
        )

        return ((await session.exec(incoming_query)).first() or 0.0) - (
            (await session.exec(outgoing_query)).first() or 0.0
        )


class BankAccountOperation(SQLModel, table=True):
    """
    source_account_id is None -> operation is deposit
    destination_account_id is None -> operation is withdrawal
    """

    __tablename__ = "bank_account_operation"
    operation_id: int = Field(primary_key=True)
    operation_date: datetime = Field(default_factory=datetime.now)
    amount: float
    title: str
    description: str
    source_account_id: int | None = Field(foreign_key="bank_account.id")
    destination_account_id: int | None = Field(foreign_key="bank_account.id")
