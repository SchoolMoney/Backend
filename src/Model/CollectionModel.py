from datetime import date
from typing import Optional

from pydantic import BaseModel, field_validator

from src.Model.CollectionStatusEnum import CollectionStatusEnum
from src.SQL.Enum import CollectionStatus


class CollectionModel(BaseModel):
    id: int
    logo_path: str
    name: str
    description: str
    start_date: date
    end_date: date
    status: CollectionStatusEnum
    price: float
    class_group_id: int
    bank_account_id: int
    owner_id: int
    withdrawn_money: float

    class Config:
        orm_mode = True

class CreateCollection(BaseModel):
    logo_path: str
    name: str
    description: str
    start_date: date
    end_date: date | None = None
    status: CollectionStatusEnum
    price: float
    class_group_id: int
    bank_account_id: int
    owner_id: int
    
class UpdateCollection(BaseModel):
    id: int
    logo_path: str
    name: str
    description: str
    start_date: date
    end_date: date
    status: CollectionStatusEnum
    price: float
    class_group_id: int
    bank_account_id: int
    owner_id: int
    withdrawn_money: float

class CollectionChildrenList(BaseModel):
    child_id: int
    child_name: str
    child_surname: str
    requester_name: Optional[str] = None
    requester_surname: Optional[str] = None
    operation: Optional[int] = None
    operation_date: Optional[date] = None
