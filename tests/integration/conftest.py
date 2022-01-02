import asyncio
from typing import Iterator, Generator

import pytest
from beanie import init_beanie
from httpx import AsyncClient
from asgi_lifespan import LifespanManager
from motor import motor_asyncio

from beanie_fastapi_demo.main import app, Settings
from beanie_fastapi_demo.models import __beanie_documents__


@pytest.fixture(autouse=True)
async def clear_db():
    client = motor_asyncio.AsyncIOMotorClient(Settings().mongo_dsn)
    await init_beanie(
        database=client.beanie_db,
        document_models=__beanie_documents__
    )
    yield None

    for model in __beanie_documents__:
        await model.get_motor_collection().drop()
        await model.get_motor_collection().drop_indexes()


@pytest.fixture()
async def client() -> Iterator[AsyncClient]:
    async with LifespanManager(app):
        async with AsyncClient(app=app, base_url="http://test") as async_client:
            yield async_client
