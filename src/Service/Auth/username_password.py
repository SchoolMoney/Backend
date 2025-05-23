from fastapi import HTTPException, status
import src.Service.Auth.Models as AuthModels
import src.Model.UserAccount as UserModel
import src.SQL as SQL
from .jwt import generate_access_token
from .helpers import get_user_account
from src.SQL.Enum.AccountStatus import ENABLED


async def user_login(
    login_form: UserModel.Login,
    sql_session: SQL.AsyncSession,
) -> AuthModels.Token:
    if login_form is None or login_form.username is None or login_form.password is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid login form"
        )

    user = await get_user_account(sql_session, username=login_form.username)

    if user is None or user.password != login_form.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User is unauthorized"
        )

    if user.status != ENABLED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User login is locked. Please contact administrator"
        )

    return generate_access_token(user)
