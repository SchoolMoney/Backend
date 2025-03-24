from pydantic import BaseModel, Field
import bcrypt
from src.SQL.Enum.AccountStatus import ENABLED
from src.SQL.Enum.Privilege import STANDARD_USER
from src.config import PASSWORD_HASH_SALT


def hash_password(password: str) -> str:
    return bcrypt.hashpw(
        password.encode(),
        PASSWORD_HASH_SALT.encode(),
    ).decode()


class User(BaseModel):
    id: int
    username: str
    email: str | None
    privilege: int = Field(default=STANDARD_USER)
    status: int = Field(default=ENABLED)


class Login(BaseModel):
    username: str
    password: str

    def __init__(self, **data):
        super().__init__(**data)
        self.password = hash_password(self.password)


class RegisterUser(Login):
    pass
