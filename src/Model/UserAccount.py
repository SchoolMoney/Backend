from pydantic import BaseModel, Field
import src.SQL.Enum.AccountStatus as AccountStatus
import src.SQL.Enum.Privilege as Privilege


class User(BaseModel):
    id: int
    username: str
    email: str | None
    privilege: int = Field(default=Privilege.STANDARD_USER)
    status: int = Field(default=AccountStatus.ENABLED)


class RegisterUser(BaseModel):
    username: str
    password: str
