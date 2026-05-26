from contextlib import asynccontextmanager

from fastapi import FastAPI

from database.db import Sqlbase


@asynccontextmanager
async def lifespan(app_obj: FastAPI):
    await Sqlbase.init_pool()
    yield
    await Sqlbase.close_pool()


app = FastAPI(lifespan=lifespan)
