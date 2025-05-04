from sqlmodel import SQLModel, Field
import src.SQL.Enum.ParentRole as ParentRole
import string
import random


def generate_random_code(length=6):
    return "".join(
        random.choices("".join([string.ascii_uppercase, string.digits]), k=length)
    )


class ClassGroup(SQLModel, table=True):
    """
    Represents a group of children. Each group has a name and description.
    """

    __tablename__ = "class_group"
    id: int = Field(primary_key=True)
    name: str = Field(unique=True)
    description: str
    access_code: str | None = Field(default_factory=generate_random_code)


class ParentGroupRole(SQLModel, table=True):
    """
    Represents parent's role in the group. Each parent can have different role in different groups.
    """

    __tablename__ = "parent_group_role"
    class_group_id: int = Field(primary_key=True, foreign_key="class_group.id")
    parent_id: int = Field(primary_key=True, foreign_key="parent.id")
    role: int = Field(default=ParentRole.MEMBER)
