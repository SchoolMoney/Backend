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


class ChangePassword(BaseModel):
    old_password: str
    new_password: str

    def __init__(self, **data):
        super().__init__(**data)
        self.old_password = hash_password(self.old_password)
        self.new_password = hash_password(self.new_password)

    def is_password_same(self) -> bool:
        return self.old_password == self.new_password


class UpdateIdentity(BaseModel):
    username: str


class UpdateParentProfile(BaseModel):
    name: str
    surname: str
    phone: str
    city: str
    street: str
    house_number: str
