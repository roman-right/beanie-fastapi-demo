import pytest
from httpx import AsyncClient

from tests.integration.factory import create_note

pytestmark = pytest.mark.asyncio


async def test_get_note_by_id(client: AsyncClient) -> None:
    note = await create_note()

    response = await client.get(f"/v1/notes/{note.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == note.title
    assert data["text"] == note.text
    assert data["tag_list"] == note.tag_list


async def test_get_notes(client: AsyncClient) -> None:
    # as there are no notes, the api should return an empty list
    response = await client.get("/v1/notes/")
    assert response.status_code == 200
    assert len(response.json()) == 0

    # create notes
    await create_note()
    await create_note()

    # the api should now return two notes
    response = await client.get("/v1/notes/")
    assert response.status_code == 200
    assert len(response.json()) == 2

