from typing import List

from beanie.fields import PydanticObjectId
from fastapi import APIRouter, HTTPException, Depends

from models import Note, Tag, AggregationResponseItem, StatusModel, Statuses

notes_router = APIRouter()


async def get_note(note_id: PydanticObjectId) -> Note:
    note = await Note.get(note_id)
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


# CRUD

@notes_router.post("/notes/", response_model=Note)
async def create_note(note: Note):
    await note.create()
    return note


@notes_router.get("/notes/{note_id}", response_model=Note)
async def get_note_by_id(note: Note = Depends(get_note)):
    return note


@notes_router.put("/notes/{note_id}/add_tag", response_model=Note)
async def add_tag(tag: Tag, note: Note = Depends(get_note)):
    await note.update(update_query={"$push": {"tag_list": tag.dict()}})
    return note


@notes_router.delete("/notes/{note_id}", response_model=StatusModel)
async def get_note_by_id(note: Note = Depends(get_note)):
    await note.delete()
    return StatusModel(status=Statuses.DELETED)


# LISTS

@notes_router.get("/notes/", response_model=List[Note])
async def get_all_notes():
    return await Note.find_all().to_list()


@notes_router.get("/notes/by_tag/{tag_name}", response_model=List[Note])
async def filter_notes_by_tag(tag_name: str):
    return await Note.find_many({"tag_list.name": tag_name}).to_list()


# AGGREGATIONS

@notes_router.get("/notes/aggregate/by_tag_name", response_model=List[AggregationResponseItem])
async def filter_notes_by_tag():
    return await Note.aggregate(
        aggregation_query=[
            {"$unwind": "$tag_list"},
            {"$group": {"_id": "$tag_list.name", "total": {"$sum": 1}}}
        ],
        item_model=AggregationResponseItem
    ).to_list()


@notes_router.get("/notes/aggregate/by_tag_color", response_model=List[AggregationResponseItem])
async def filter_notes_by_tag():
    return await Note.aggregate(
        aggregation_query=[
            {"$unwind": "$tag_list"},
            {"$group": {"_id": "$tag_list.color", "total": {"$sum": 1}}}
        ],
        item_model=AggregationResponseItem
    ).to_list()
