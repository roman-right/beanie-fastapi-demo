from typing import List

from beanie import PydanticObjectId
from fastapi import APIRouter, HTTPException, Depends

from beanie_fastapi_demo.models.note import Note, Tag, AggregationResponseItem, StatusModel, Statuses

router = APIRouter(prefix="/notes", tags=["note"])


async def get_note(note_id: PydanticObjectId) -> Note:
    note = await Note.get(note_id)
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@router.post("/", response_model=Note)
async def create_note(note: Note):
    await note.create()
    return note


@router.get("/{note_id}", response_model=Note)
async def get_note_by_id(note: Note = Depends(get_note)):
    return note


@router.put("/{note_id}/add_tag", response_model=Note)
async def add_tag(tag: Tag, note: Note = Depends(get_note)):
    await note.update(update_query={"$push": {"tag_list": tag.dict()}})
    return note


@router.delete("/{note_id}", response_model=StatusModel)
async def get_note_by_id(note: Note = Depends(get_note)):
    await note.delete()
    return StatusModel(status=Statuses.DELETED)


@router.get("/", response_model=List[Note])
async def get_all_notes():
    return await Note.find_all().to_list()


@router.get("/by_tag/{tag_name}", response_model=List[Note])
async def filter_notes_by_tag(tag_name: str):
    return await Note.find_many({"tag_list.name": tag_name}).to_list()


@router.get("/aggregate/by_tag_name", response_model=List[AggregationResponseItem])
async def filter_notes_by_tag_name():
    return await Note.aggregate(
        aggregation_query=[
            {"$unwind": "$tag_list"},
            {"$group": {"_id": "$tag_list.name", "total": {"$sum": 1}}}
        ],
        item_model=AggregationResponseItem
    ).to_list()


@router.get("/aggregate/by_tag_color", response_model=List[AggregationResponseItem])
async def filter_notes_by_tag_color():
    return await Note.aggregate(
        aggregation_query=[
            {"$unwind": "$tag_list"},
            {"$group": {"_id": "$tag_list.color", "total": {"$sum": 1}}}
        ],
        item_model=AggregationResponseItem
    ).to_list()
