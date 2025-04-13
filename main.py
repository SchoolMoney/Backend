import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import src.config as config
import src.SQL as SQL
from src.SQL.data_insert import insert_data
import src.router as router


@asynccontextmanager
async def app_lifespan(app: FastAPI):
    SQL.Tables.create_table()
    await insert_data()
    yield


app = FastAPI(
    lifespan=app_lifespan,
    title=config.APP_TITLE,
    description=config.APP_DESCRIPTION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        config.CORS_FRONTEND,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    router.child_router,
    prefix=f"{config.API_PREFIX}/child",
    tags=["child"]
)
app.include_router(
    router.user_router,
    prefix=f"{config.API_PREFIX}/user",
    tags=["user"],
)
app.include_router(
    router.auth_router,
    prefix=f"{config.API_PREFIX}/auth",
    tags=["auth"],
)

app.include_router(
    router.parent_router,
    prefix=f"{config.API_PREFIX}/parent",
    tags=["parent"],
)

app.include_router(
    router.class_group_router,
    prefix=f"{config.API_PREFIX}/class_group",
    tags=["class_group"],
)

app.include_router(
    router.collection_router,
    prefix=f"{config.API_PREFIX}/collection",
    tags=["collection"],
)

app.include_router(
    router.bank_account_router,
    prefix=f"{config.API_PREFIX}/bank_account",
    tags=["bank_account"],
)

if __name__ == "__main__":
    uvicorn.run(
        app,
        host=config.API_ADDRESS,
        port=config.API_PORT,
    )
