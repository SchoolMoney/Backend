from sqlmodel import SQLModel, Field
from datetime import date


class Collection(SQLModel, table=True):
    """
    To return money to parent,
        cashier needs to create a refund operation for each participant (Update CollectionOperation table)
    To discharge child from collection,
        parent needs to create a discharge operation for each participant (Insert CollectionOperation entry)
    """

    __tablename__ = "collection"
    id: int = Field(primary_key=True)
    name: str
    description: str
    start_date: date = Field(default=date.today())
    end_date: date | None
    price: float
    class_group_id: int = Field(foreign_key="class_group.id")
    bank_account_id: int = Field(foreign_key="bank_account.id")
    owner_id: int = Field(foreign_key="parent.id")


class CollectionDocuments(SQLModel, table=True):
    """
    Document can be added to collection to provide additional information about it, e.g. recipes
    """

    __tablename__ = "collection_documents"
    document_id: int = Field(primary_key=True)
    collection_id: int = Field(foreign_key="collection.id")
    document_name: str
    document_path: str


class CollectionOperation(SQLModel, table=True):
    """
    operation_type (defined in src.SQL.Enum.CollectionOperationType):
        - PAY - payed for child's participation in collection
        - DISCHARGE - parent discharged child from collection
        - REFUND - Cashier returned money to parent

    creating a pay or refund operation should also create an appropriate bank account operation
    """

    __tablename__ = "collection_operation"
    child_id: int = Field(primary_key=True, foreign_key="child.id")
    collection_id: int = Field(primary_key=True, foreign_key="collection.id")
    operation_date: date
    requester_id: int = Field(foreign_key="parent.id")
    operation_type: int
