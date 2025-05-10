from datetime import datetime

from pydantic import BaseModel


class BankAccountOperation(BaseModel):
    operation_id: int
    operation_date: datetime
    amount: float
    title: str
    description: str
    source_account_id: int | None = None
    destination_account_id: int | None = None


class BankAccountBalance(BaseModel):
    account_id: int
    balance: float
