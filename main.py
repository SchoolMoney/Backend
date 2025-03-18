import uvicorn
from fastapi import FastAPI
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

app.include_router(router.user_router)
app.include_router(router.class_group_router)
app.include_router(router.child_router)

if __name__ == "__main__":
    uvicorn.run(
        app,
        host=config.API_ADDRESS,
        port=config.API_PORT,
    )
