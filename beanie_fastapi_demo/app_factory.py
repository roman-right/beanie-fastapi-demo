import motor
from beanie.general import init_beanie
from fastapi import FastAPI
from pydantic import BaseSettings

from models import Note
from routes import notes_router

app = FastAPI()


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
    # CREATE MOTOR CLIENT
    client = motor.motor_asyncio.AsyncIOMotorClient(
        Settings().mongo_dsn, serverSelectionTimeoutMS=100
    )

    # INIT BEANIE
    await init_beanie(client.beanie_db, document_models=[Note])

    # ADD ROUTES
    app.include_router(notes_router, prefix="/v1", tags=["notes"])
