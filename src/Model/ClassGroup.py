from pydantic import BaseModel


class UpdateClassGroup(BaseModel):
    id: int
    name: str
    description: str


class AddClassGroup(BaseModel):
    name: str
    description: str