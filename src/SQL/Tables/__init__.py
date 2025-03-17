from src.config import DB_DROP_EXISTING_TABLES
from src.SQL.connection import PG_CONNECTION_STRING
from sqlalchemy import create_engine
from sqlmodel import SQLModel
from src.SQL.Tables.Financial import BankAccount, BankAccountOperation  # noqa: F401
from src.SQL.Tables.Collection import Collection, CollectionOperation  # noqa: F401
from src.SQL.Tables.OrganizationUnit import ClassGroup, ParentGroupRole  # noqa: F401
from src.SQL.Tables.People import Parent, Child, UserAccount  # noqa: F401
import src.config as config


def create_table(
    drop_existing: bool = DB_DROP_EXISTING_TABLES,
) -> None:
    engine = create_engine(
        PG_CONNECTION_STRING.format(
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            address=config.DB_ADDRESS,
            port=config.DB_PORT,
            db_name=config.DB_NAME,
        ),
        echo=True,
    )
    if drop_existing:
        SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
