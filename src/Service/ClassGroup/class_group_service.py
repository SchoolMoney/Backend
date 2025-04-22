import src.SQL as SQL

from src.Model.ClassGroup import AddClassGroup, ChangeClassGroupCashier

from fastapi import HTTPException, status
from src.SQL.Tables import ClassGroup
from src.repository import class_group_repository, parent_repository, parent_group_role_repository
import src.SQL.Enum.ParentRole as ParentRole

async def create(
    sql_session: SQL.AsyncSession, class_group_data: AddClassGroup
) -> ClassGroup:
    class_group = await class_group_repository.get_by_name(
        sql_session, class_group_data.name
    )
    if class_group:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Class group with specific name already exists"
        )
    
        
    class_group = SQL.Tables.ClassGroup(**class_group_data.model_dump())
    
    return await class_group_repository.create(sql_session, class_group)
  

async def change_cashier(
    sql_session: SQL.AsyncSession, class_group_id: int, request: ChangeClassGroupCashier
):
    class_group = await class_group_repository.get_by_id(sql_session, class_group_id)
    if not class_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Class group with ID {class_group_id} not found"
        )
        
    parent = await parent_repository.get_by_id(sql_session, request.parent_id)
    if not parent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Parent with ID {request.parent_id} not found"
        )
        
    parent_group_role = await parent_group_role_repository.get(sql_session, class_group_id, request.parent_id)
    if not parent_group_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Parent is not a member of the class"
        )
        
    cashier_group_role = await parent_group_role_repository.get_cashier(sql_session, class_group_id)
    if cashier_group_role:
        cashier_group_role.role = ParentRole.MEMBER
        await sql_session.commit()
        await sql_session.refresh(cashier_group_role)
        
    parent_group_role.role = ParentRole.CASHIER
    await sql_session.commit()
    await sql_session.refresh(parent_group_role)
    
