from pydantic import BaseModel


class BankAccount(BaseModel):
    account_number: str
    is_locked: bool | None = False