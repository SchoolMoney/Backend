from sqlmodel import SQLModel, Field
from datetime import date
from src.Model.UserAccount import User
from src.Model.PeopleModel import ParentModel


class UserAccount(SQLModel, User, table=True):
    """
    User account is used to authenticate user in the system. It can be associated with parent or employee.
    Privilege is used to determine user's role in the system. (defined in src.SQL.Enum.Privilege)
        - STANDARD_USER
        - ADMIN
    Status is used to determine if user can log in to the system. (defined in src.SQL.Enum.AccountStatus)
        - ENABLED
        - DISABLED
        - LOCKED
    """

    __tablename__ = "user_account"
    id: int = Field(primary_key=True)
    username: str = Field(index=True, unique=True)
    password: str


class Child(SQLModel, table=True):
    """
    Child is a person who is a participant of the class group. It can be associated with only one group.
    A child can be associated with more than one parent via Parenthood table.
    """

    __tablename__ = "child"
    id: int = Field(primary_key=True)
    name: str
    surname: str
    birth_date: date
    group_id: int = Field(foreign_key="class_group.id", index=True)


class Parenthood(SQLModel, table=True):
    """
    Relationship between parent and child. It is used to determine who is responsible for child.
    """

    __tablename__ = "parenthood"
    parent_id: int = Field(primary_key=True, foreign_key="parent.id")
    child_id: int = Field(primary_key=True, foreign_key="child.id")


class Parent(SQLModel, ParentModel, table=True):
    """
    Parent is a person who is responsible for child. It can be associated with more than one child via Parenthood table.
    Parent must be associated with user account.
    """

    __tablename__ = "parent"
    id: int = Field(primary_key=True)
    account_id: int = Field(foreign_key="user_account.id", unique=True)

