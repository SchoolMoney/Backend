import src.SQL as SQL

from src.Model.ClassGroup import (
    AddClassGroup,
    ChangeClassGroupCashier,
    UpdateClassGroup,
)

from fastapi import HTTPException, status
from src.SQL.Tables import ClassGroup, ParentGroupRole
from src.repository import (
    class_group_repository,
    parent_repository,
    parent_group_role_repository,
)
import src.SQL.Enum.ParentRole as ParentRole


async def create(
    sql_session: SQL.AsyncSession, class_group_data: AddClassGroup, user_id: int
) -> ClassGroup:
    class_group = await class_group_repository.get_by_name(
        sql_session, class_group_data.name
    )
    if class_group:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Class group with specific name already exists",
        )

    user_parent_profile = await parent_repository.get_by_user_account(
        sql_session, user_id
    )

    class_group = SQL.Tables.ClassGroup(**class_group_data.model_dump())
    class_group = await class_group_repository.create(sql_session, class_group)

    # Class creator must be cashier automatically
    await parent_group_role_repository.create(
        sql_session,
        ParentGroupRole(
            class_group_id=class_group.id,
            parent_id=user_parent_profile.id,
            role=ParentRole.CASHIER,
        ),
    )

    return class_group


async def update(
    sql_session: SQL.AsyncSession,
    class_group_id: int,
    update_data: UpdateClassGroup,
    user_id: int,
):
    class_group_with_same_name = await class_group_repository.get_by_name(
        sql_session, update_data.name
    )
    if class_group_with_same_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Class group with name '{update_data.name}' already exists",
        )

    class_group = await class_group_repository.get_by_id(sql_session, class_group_id)
    if not class_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Class group with ID {class_group_id} not found",
        )

    user_parent_profile = await parent_repository.get_by_user_account(
        sql_session, user_id
    )
    if not user_parent_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Parent profile for user ID {user_id} not found",
        )

    user_group_role = await parent_group_role_repository.get(
        sql_session, class_group_id, user_parent_profile.id
    )
    if not user_group_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not a member of the class group",
        )

    if user_group_role.role is not ParentRole.CASHIER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have the permissions to update this class group. You must have cashier role",
        )

    updated_fields = update_data.model_dump(exclude_unset=True)
    for key, value in updated_fields.items():
        setattr(class_group, key, value)

    await sql_session.commit()
    await sql_session.refresh(class_group)
    return class_group


async def change_cashier(
    sql_session: SQL.AsyncSession,
    class_group_id: int,
    request: ChangeClassGroupCashier,
    user_id: int,
):
    class_group = await class_group_repository.get_by_id(sql_session, class_group_id)
    if not class_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Class group with ID {class_group_id} not found",
        )

    parent = await parent_repository.get_by_id(sql_session, request.parent_id)
    if not parent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Parent with ID {request.parent_id} not found",
        )

    user_parent_profile = await parent_repository.get_by_user_account(
        sql_session, user_id
    )
    if not user_parent_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Parent profile not found"
        )

    parent_group_role = await parent_group_role_repository.get(
        sql_session, class_group_id, request.parent_id
    )
    if not parent_group_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Parent is not a member of the class",
        )

    cashier_group_role = await parent_group_role_repository.get_cashier(
        sql_session, class_group_id
    )
    if cashier_group_role.parent_id is not user_parent_profile.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"You are not cashier in the class",
        )

    cashier_group_role.role = ParentRole.MEMBER
    await sql_session.commit()
    await sql_session.refresh(cashier_group_role)

    parent_group_role.role = ParentRole.CASHIER
    await sql_session.commit()
    await sql_session.refresh(parent_group_role)


async def delete(sql_session: SQL.AsyncSession, class_group_id: int, user_id: int):
    class_group = await class_group_repository.get_by_id(sql_session, class_group_id)
    if not class_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Class group with ID {class_group_id} not found",
        )

    user_parent_profile = await parent_repository.get_by_user_account(
        sql_session, user_id
    )
    if not user_parent_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Parent profile for user ID {user_id} not found",
        )

    user_group_role = await parent_group_role_repository.get(
        sql_session, class_group_id, user_parent_profile.id
    )
    if not user_group_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not a member of the class group",
        )

    if user_group_role.role is not ParentRole.CASHIER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have the permissions to delete this class group. You must have cashier role",
        )

    await class_group_repository.delete(sql_session, class_group_id)
