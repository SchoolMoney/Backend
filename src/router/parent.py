from typing import Annotated, List
from fastapi import APIRouter, Depends, logger, status, HTTPException
from sqlmodel import Sequence

from src.Model.ParentBasicInfo import ParentBasicInfo
from src.repository import parent_repository
from src.Model.PeopleModel import ParentModel
import src.SQL as SQL
import src.Service.Auth as Auth
from src.Service.IBAN_generator.iban_db_service import create_bank_account
from src.SQL.Enum.Privilege import ADMIN_USER
from src.SQL.Tables.People import Parent
import src.Model.UserAccount as UserModel

parent_router = APIRouter()


@parent_router.post("/", response_model=SQL.Tables.People.Parent)
async def create(
    user: Annotated[Auth.AuthorizedUser, Depends(Auth.authorized_user())],
    sql_session: Annotated[SQL.AsyncSession, Depends(SQL.async_session_generator)],
    parent_entry: ParentModel,
) -> SQL.Tables.People.Parent:
    parent_entry.is_valid_number()

    bank_account = await create_bank_account(sql_session)

    parent_record = SQL.Tables.People.Parent(
        **{
            **parent_entry.model_dump(),
            "account_id": user.user_id,
            "bank_account_id": bank_account.id
        }
    )
    sql_session.add(parent_record)
    try:
        await sql_session.commit()
    except Exception as e:
        if e.orig.pgcode == "23505":
            await sql_session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You are already a parent",
            )
        raise e

    return parent_record


@parent_router.put("/", response_model=SQL.Tables.People.Parent)
async def update(
    user: Annotated[Auth.AuthorizedUser, Depends(Auth.authorized_user())],
    sql_session: Annotated[SQL.AsyncSession, Depends(SQL.async_session_generator)],
    parent_entry: ParentModel,
) -> SQL.Tables.People.Parent:
    parent_entry.is_valid_number()

    if (modified_record := (await sql_session.exec(
            SQL.select(SQL.Tables.People.Parent).filter(
                SQL.Tables.People.Parent.account_id == user.user_id))).first()) is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are not a parent",
        )

    for field in parent_entry.model_dump():
        setattr(modified_record, field, getattr(parent_entry, field))

    try:
        await sql_session.commit()
    except Exception as e:
        raise e
    await sql_session.refresh(modified_record)
    return modified_record


@parent_router.get("/", response_model=List[Parent])
async def get(
    user: Annotated[Auth.AuthorizedUser, Depends(Auth.authorized_user(ADMIN_USER))],
    sql_session: Annotated[SQL.AsyncSession, Depends(SQL.async_session_generator)],
) -> Sequence[Parent]:
    try:
        return await parent_repository.get_all(sql_session)
    except Exception as e:
        logger.logger.error(f"Error retrieving parents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve parents"
        )

@parent_router.get("/all_basic_info", response_model=List[ParentBasicInfo])
async def get_all_basic_info(
    user: Annotated[Auth.AuthorizedUser, Depends(Auth.authorized_user())],
    sql_session: Annotated[SQL.AsyncSession, Depends(SQL.async_session_generator)],
) -> List[ParentBasicInfo]:
    try:
        return await parent_repository.get_all_basic_info(sql_session)
    except Exception as e:
        logger.logger.error(f"Error retrieving all basic info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve all basic info"
        )

@parent_router.get("/user", response_model=SQL.Tables.People.Parent)
async def get_by_logged_user(
    user: Annotated[Auth.AuthorizedUser, Depends(Auth.authorized_user())],
    sql_session: Annotated[SQL.AsyncSession, Depends(SQL.async_session_generator)],
) -> SQL.Tables.People.Parent:
    try:
        return await parent_repository.get_by_user_account(sql_session, user.user_id)
    except Exception as e:
        logger.logger.error(f"Error retrieving user's parent profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user's parent profile"
        )


@parent_router.put("/user")
async def update_logged_user_profile(
    user: Annotated[Auth.AuthorizedUser, Depends(Auth.authorized_user())],
    parent_profile: UserModel.UpdateParentProfile,
    sql_session: Annotated[SQL.AsyncSession, Depends(SQL.async_session_generator)],
):
    try:
        updated_profile = SQL.Tables.Parent(**parent_profile.model_dump())
        await parent_repository.update_by_user(sql_session, updated_profile, user.user_id)
    except Exception as e:
        logger.logger.error(f"Error updating user's parent profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to updating user's parent profile"
        )
