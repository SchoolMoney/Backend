from fastapi import HTTPException, status
import src.SQL as SQL
from .Redis import AuthorizedUser, RedisAuth
from .Models import Token
from .helpers import get_user_account
from .jwt import generate_access_token


def user_logout(user: AuthorizedUser):
    redis_client = RedisAuth()
    redis_client.invalidate_access_token(user.access_token)


async def refresh_token(
    refresh_token: str,
    sql_session: SQL.AsyncSession,
) -> Token:
    redis = RedisAuth()
    if (owner_id := redis.get_refresh_token_owner(refresh_token)) is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )
    redis.invalidate_refresh_token(refresh_token)
    user = await get_user_account(sql_session, user_id=owner_id)
    return generate_access_token(user)
