from pydantic import BaseModel, Field


class BankAccount(BaseModel):
    id: int
    account_number: str
    is_locked: bool | None = False
    balance: float | None = 0.0


class ExternalBankAccountOperation(BaseModel):
    bank_account_id: int | None = Field(default=None)
    account_number: str | None = Field(default=None)
    amount: float
