from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: str
    expires: int


class AccessTokenData(BaseModel):
    user_id: int
    username: str
    privilege: int
    expires: int
    refresh_token: str


class RefreshTokenData(BaseModel):
    expires: int
    user_id: int
