from pydantic import BaseModel
from redis import Redis
import datetime
from typing import ClassVar
import src.config as config
import src.Service.Auth.Models as AuthModels


class RedisSingleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class AuthorizedUser(BaseModel):
    user_id: int
    user_privilege: int
    access_token: str


class UserAccessTokenDetails(BaseModel):
    user_id: int
    user_privilege: int
    access_token: str
    refresh_token: str

    def to_redis_value(self) -> str:
        return f"{RedisAuth.access_token_type}:{self.user_id}:{self.user_privilege}:{self.access_token}:{self.refresh_token}"

    def get_user(self) -> AuthorizedUser:
        return AuthorizedUser(user_id=self.user_id, user_privilege=self.user_privilege)

    @classmethod
    def create_from_redis_value(cls: "UserAccessTokenDetails", value: str):
        token_type, user_id, user_privilege, access_token, refresh_token = value.split(
            ":"
        )
        if token_type != RedisAuth.access_token_type:
            raise ValueError("Invalid token type")
        return cls(
            user_id=int(user_id),
            user_privilege=int(user_privilege),
            access_token=access_token,
            refresh_token=refresh_token,
        )


class RedisAuth(metaclass=RedisSingleton):
    access_token_type: ClassVar[str] = "access_token"
    refresh_token_type: ClassVar[str] = "refresh_token"

    def __init__(self):
        self.redis = Redis(
            host=config.REDIS_HOST,
            port=config.REDIS_PORT,
            db=config.REDIS_DB,
            decode_responses=True,
        )

    def register_token(
        self,
        access_token: str,
        token_data: AuthModels.AccessTokenData,
    ) -> None:
        current_time = int(datetime.datetime.now().timestamp())
        user_id = token_data.user_id
        refresh_token = token_data.refresh_token

        access_token_details = UserAccessTokenDetails(
            user_id=user_id,
            user_privilege=token_data.privilege,
            access_token=access_token,
            refresh_token=refresh_token,
        )

        # Register token in Redis
        self.redis.set(access_token, access_token_details.to_redis_value())
        self.redis.expire(access_token, config.ACCESS_TOKEN_EXPIRATION_PERIOD)

        access_token_set_name = self.__get_user_tokens_set_name(user_id)
        self.__cleanup_sorted_set(access_token_set_name)
        # Register token in user's token in sorted set - for future token invalidation
        self.redis.zadd(
            access_token_set_name,
            {access_token: (current_time + config.ACCESS_TOKEN_EXPIRATION_PERIOD)},
        )

        refresh_token_set_name = self.__get_user_refresh_tokens_set_name(user_id)
        self.__cleanup_sorted_set(refresh_token_set_name)
        # Register refresh token in Redis sorted set
        self.redis.set(refresh_token, f"{self.refresh_token_type}:{user_id}")
        self.redis.expire(refresh_token, config.REFRESH_TOKEN_EXPIRATION_PERIOD)

        self.redis.zadd(
            refresh_token_set_name,
            {refresh_token: (current_time + config.REFRESH_TOKEN_EXPIRATION_PERIOD)},
        )

    def get_refresh_token_owner(self, token: str) -> int | None:
        if (redis_value := self.redis.get(token)) is None:
            return

        token_type, user_id = redis_value.split(":")
        if token_type != self.refresh_token_type:
            raise ValueError("Invalid token type")

        return int(user_id)

    def get_owner_details(self, token: str) -> UserAccessTokenDetails:
        if (redis_value := self.redis.get(token)) is None:
            raise ValueError("Token not found")

        return UserAccessTokenDetails.create_from_redis_value(redis_value)

    def invalidate_access_token(self, token: str) -> None:
        # Get user_id from token - if token is not in Redis, it is already invalidated
        token_details = self.get_owner_details(token)

        access_set_name = self.__get_user_tokens_set_name(token_details.user_id)

        self.redis.delete(token)
        self.redis.zrem(access_set_name, token)
        self.__cleanup_sorted_set(access_set_name)

        refresh_set_name = self.__get_user_refresh_tokens_set_name(
            token_details.user_id
        )

        self.redis.delete(token_details.refresh_token)
        self.redis.zrem(refresh_set_name, token_details.refresh_token)
        self.__cleanup_sorted_set(refresh_set_name)

    def invalidate_refresh_token(self, token: str) -> None:
        if (redis_value := self.redis.get(token)) is None:
            return

        token_type, user_id = redis_value.split(":")
        if token_type != self.refresh_token_type:
            raise ValueError("Invalid token type")

        access_set_name = self.__get_user_tokens_set_name(int(user_id))
        self.redis.zrem(access_set_name, token)
        self.__cleanup_sorted_set(access_set_name)

        self.redis.delete(token)

    def __cleanup_sorted_set(self, set_name: str) -> None:
        # Remove all expired tokens
        current_time = int(datetime.datetime.now().timestamp())
        self.redis.zremrangebyscore(set_name, 0, current_time)

    def __get_user_tokens_set_name(self, user_id: int) -> str:
        return "user_{user_id}_tokens".format(user_id=user_id)

    def __get_user_refresh_tokens_set_name(self, user_id: int) -> str:
        return "user_{user_id}_refresh_tokens".format(user_id=user_id)
