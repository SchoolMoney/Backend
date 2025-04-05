from typing import Annotated
from fastapi import APIRouter, Depends, status, HTTPException
from src.Model.PeopleModel import ParentModel
import src.SQL as SQL
import src.Service.Auth as Auth
from src.Service.IBAN_generator.iban_db_service import create_bank_account

parent_profile = APIRouter()


@parent_profile.post("/parent-profile", response_model=SQL.Tables.People.Parent)
async def create_parent_profile(
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


@parent_profile.put("/parent-profile", response_model=SQL.Tables.People.Parent)
async def create_parent_profile(
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


@parent_profile.get("/parent-profile", response_model=SQL.Tables.People.Parent)
async def create_parent_profile(
        user: Annotated[Auth.AuthorizedUser, Depends(Auth.authorized_user())],
        sql_session: Annotated[SQL.AsyncSession, Depends(SQL.async_session_generator)],
) -> SQL.Tables.People.Parent:
    if (parent_record := (await sql_session.exec(
            SQL.select(SQL.Tables.People.Parent).filter(
                SQL.Tables.People.Parent.account_id == user.user_id))).first()) is None:
        raise HTTPException(
            status_code=status.HTTP_204_NO_CONTENT,
            detail="You are not a parent",
        )

    try:
        await sql_session.commit()
    except Exception as e:
        raise e

    return parent_record
