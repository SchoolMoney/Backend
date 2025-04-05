import datetime

from pydantic import BaseModel

class Collection(BaseModel):
    name:str
    description:str
    logo_path:str | None = None
    start_date: datetime.datetime
    end_date: datetime.datetime
    status: int | None = 0
    price: float
    class_group_id: int
