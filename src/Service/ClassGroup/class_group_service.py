import src.SQL as SQL

from src.Model.ClassGroup import AddClassGroup

from fastapi import HTTPException, status
from src.SQL.Tables import ClassGroup
from src.repository import class_group_repository

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