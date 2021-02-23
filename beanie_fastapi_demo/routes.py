from typing import List

from fastapi import APIRouter
from beanie.fields import PydanticObjectId

from models import Note, Tag, AggregationResponseItem

notes_router = APIRouter()


@notes_router.post("/notes/", response_model=Note)
async def create_note(note: Note):
    await note.create()
    return note


@notes_router.get("/notes/", response_model=List[Note])
async def get_all_notes():
    return await Note.all().to_list()


@notes_router.get("/notes/{note_id}", response_model=Note)
async def get_note_by_id(note_id: PydanticObjectId):
    return await Note.get(note_id)


@notes_router.post("/notes/{note_id}/add_tag", response_model=Note)
async def add_tag(note_id: PydanticObjectId, tag: Tag):
    note = await Note.get(note_id)
    await note.update(update_query={"$push": {"tag_list": tag.dict()}})
    return note


@notes_router.get("/notes/by_tag/{tag_name}", response_model=List[Note])
async def filter_notes_by_tag(tag_name: str):
    return await Note.find({"tag_list.name": tag_name}).to_list()


@notes_router.get("/notes/aggregate/by_tag_name", response_model=List[AggregationResponseItem])
async def filter_notes_by_tag():
    return await Note.aggregate(
        query=[
            {"$unwind": "$tag_list"},
            {"$group": {"_id": "$tag_list.name", "total": {"$sum": 1}}}
        ],
        item_model=AggregationResponseItem
    ).to_list()


@notes_router.get("/notes/aggregate/by_tag_color", response_model=List[AggregationResponseItem])
async def filter_notes_by_tag():
    return await Note.aggregate(
        query=[
            {"$unwind": "$tag_list"},
            {"$group": {"_id": "$tag_list.color", "total": {"$sum": 1}}}
        ],
        item_model=AggregationResponseItem
    ).to_list()
