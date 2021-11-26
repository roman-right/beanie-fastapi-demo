from motor import motor_asyncio
from beanie import init_beanie
from fastapi import FastAPI
from pydantic import BaseSettings

from beanie_fastapi_demo.models import __beanie_documents__
from beanie_fastapi_demo.routes import note_router

app = FastAPI()


class Settings(BaseSettings):
    mongo_host: str = "localhost"
    mongo_port: int = 27017
    mongo_user: str = "beanie"
    mongo_pass: str = "beanie"
    mongo_db: str = "beanie_db"

    @property
    def mongo_dsn(self):
        """
        :return: The complete Data Source Name (dsn) based on settings
        """
        return f"mongodb://{self.mongo_user}:{self.mongo_pass}@{self.mongo_host}:{self.mongo_port}/{self.mongo_db}"


@app.on_event("startup")
async def app_init():
    """Initialize the application services"""
    client = motor_asyncio.AsyncIOMotorClient(Settings().mongo_dsn)
    await init_beanie(client.beanie_db, document_models=__beanie_documents__)
    app.include_router(note_router, prefix="/v1")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=10001)
