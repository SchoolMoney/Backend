from pydantic import BaseModel


class ParentBasicInfo(BaseModel):
    id: int
    first_name: str
    last_name: str
