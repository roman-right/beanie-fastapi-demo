import motor
from fastapi import FastAPI
from beanie import Collection
from pydantic import BaseSettings

from models import Note
from routes import notes_router

app = FastAPI(redoc_url="/users/redoc", openapi_url="/users/openapi.json")


class Settings(BaseSettings):
    mongo_host: str = "localhost"
    mongo_user: str = "beanie"
    mongo_pass: str = "beanie"
    mongo_db: str = "beanie_db"

    @property
    def mongo_dsn(self):
        return f"mongodb://{self.mongo_user}:{self.mongo_pass}@{self.mongo_host}:27017/{self.mongo_db}"


@app.on_event("startup")
async def app_init():
    client = motor.motor_asyncio.AsyncIOMotorClient(
        Settings().mongo_dsn, serverSelectionTimeoutMS=100
    )
    db = client.beanie_db
    Collection(
        name="notes", db=db, document_model=Note
    )

    app.include_router(notes_router, prefix="/v1", tags=["notes"])
