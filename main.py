import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import src.config as config
import src.SQL.Tables as Tables
import src.router as router


@asynccontextmanager
async def app_lifespan(app: FastAPI):
    Tables.create_table()
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
        "http://localhost:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

if __name__ == "__main__":
    uvicorn.run(
        app,
        host=config.API_ADDRESS,
        port=config.API_PORT,
    )
