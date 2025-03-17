from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession
import src.config as config

PG_CONNECTION_STRING = "postgresql://{user}:{password}@{address}:{port}/{db_name}"
PG_ASYNC_CONNECTION_STRING = (
    "postgresql+asyncpg://{user}:{password}@{address}:{port}/{db_name}"
)

async_engine = create_async_engine(
    PG_ASYNC_CONNECTION_STRING.format(
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        address=config.DB_ADDRESS,
        port=config.DB_PORT,
        db_name=config.DB_NAME,
    ),
    pool_timeout=30,
    pool_recycle=300,
    pool_size=20,
    max_overflow=40,
)

async_session_maker = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_async_session():
    async with async_session_maker() as session:
        yield session
