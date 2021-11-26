import random
import string
from typing import List

from beanie_fastapi_demo.models.note import Tag, Note


def create_random_string(number_of_chars: int = 42):
    return ''.join(random.choice(string.printable) for _ in range(number_of_chars))


async def create_note(_id: str = None,
                      title: str = None,
                      text: str = None,
                      tag_list: List[Tag] = None) -> Note:
    if title is None:
        title = "Factory Note " + create_random_string(10)
    if text is None:
        text = "This not is Created by a factory\n" + create_random_string(100)
    if tag_list is None:
        tag_list = []

    note = Note(
        _id=_id,
        title=title,
        text=text,
        tag_list=tag_list,
    )
    await note.create()
    return note
