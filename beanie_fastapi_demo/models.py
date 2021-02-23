from enum import Enum
from typing import Optional, List

from beanie import Document
from pydantic import BaseModel, Field


class TagColors(str, Enum):
    RED = "RED"
    BLUE = "BLUE"
    GREEN = "GREEN"


class Tag(BaseModel):
    name: str
    color: TagColors = TagColors.BLUE


class Note(Document):
    title: str
    text: Optional[str]
    tag_list: List[Tag] = []


class AggregationResponseItem(BaseModel):
    id: str = Field(None, alias="_id")
    total: int
