from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .Redis import UserAccessTokenDetails, RedisAuth
import src.SQL.Enum.Privilege as Privilege

bearer_auth = HTTPBearer()


def authorized_user(
    expected_privilege: int = Privilege.STANDARD_USER,
) -> UserAccessTokenDetails:
    def dependency(
        authorization: Annotated[HTTPAuthorizationCredentials, Depends(bearer_auth)],
    ) -> UserAccessTokenDetails:
        client = RedisAuth()
        try:
            owner_details = client.get_owner_details(authorization.credentials)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized"
            )

        if owner_details.user_privilege < expected_privilege:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient privilege"
            )
        return owner_details

    return dependency
