import jwt
import datetime
import src.Service.Auth.Models as AuthModels
from src.Service.Auth.Redis import RedisAuth
import src.config as config
import src.SQL as SQL


def generate_access_token(
    user: SQL.Tables.UserAccount,
) -> AuthModels.Token:
    expires = (
        int(datetime.datetime.now().timestamp()) + config.ACCESS_TOKEN_EXPIRATION_PERIOD
    )
    refresh_token = __generate_refresh_token(user.id)
    token_data = AuthModels.AccessTokenData(
        user_id=user.id,
        username=user.username,
        privilege=user.privilege,
        expires=expires,
        refresh_token=refresh_token,
    )
    token = AuthModels.Token(
        access_token=encode(token_data),
        token_type="bearer",
        refresh_token=refresh_token,
        expires=expires,
    )
    RedisAuth().register_token(token.access_token, token_data)
    return token


def encode(
    data: AuthModels.AccessTokenData | AuthModels.RefreshTokenData,
) -> str:
    return jwt.encode(data.model_dump(), config.SECRET_KEY, config.JWT_ALGORITHM)


def decode_access_token(
    token: str,
) -> AuthModels.AccessTokenData:
    return AuthModels.AccessTokenData(
        **jwt.decode(
            token,
            config.SECRET_KEY,
            config.JWT_ALGORITHM,
        )
    )


def decode_refresh_token(
    token: str,
) -> AuthModels.RefreshTokenData:
    return AuthModels.RefreshTokenData(
        **jwt.decode(
            token,
            config.SECRET_KEY,
            config.JWT_ALGORITHM,
        )
    )


def __generate_refresh_token(
    user_id: int,
    expires: int = int(datetime.datetime.now().timestamp())
    + config.REFRESH_TOKEN_EXPIRATION_PERIOD,
) -> str:
    return encode(AuthModels.RefreshTokenData(user_id=user_id, expires=expires))
