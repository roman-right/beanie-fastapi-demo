I'm excited to introduce [Beanie](https://github.com/roman-right/beanie) - Python micro ODM (Object Document Mapper) for
MongoDB!

The main component of Beanie is [Pydantic](https://pydantic-docs.helpmanual.io/) - a popular library for data parsing
and validation. It helps to implement the main feature - data structuring. Beanie `Document` - is an abstraction over
the Pydantic `BaseModel` that allows working with Python objects at the application level and JSON objects at the
database level. In the general case, one MongoDB collection is associated with one Beanie `Document`. This brings
predictability when working with the database, and at the same time preserves all the flexibility of MongoDB documents -
it is possible to represent any data structure with the Pydantic model (or even a group of structures with Optional and
Union annotations).

I'm doing quite a few pet projects: Experiments with the new technologies and Proofs of Concepts. For these purposes, I
needed a tool for working with the database that I can use immediately without a long setup. And with which I could
change the data structure frequently, adding and dropping elements here and there. This is how Beanie was born.

# Usage example

But that's a bit boring, isn't it? Now let's get to the interesting part - the usage examples. It will show how handy
this tool is. I'm deliberately omitting some additional imports and helpers here, so as not to overload the picture and
focus only on the important things. The entire working app from this article is in my GitHub
repo [beanie-fastapi-demo](https://github.com/roman-right/beanie-fastapi-demo).

As an example, I'll create a small rest-service for managing notes.

## Installation

```shell
pip install beanie
```

OR

```shell
poetry add beanie
```

## Data model

The package is installed. Now we're ready to go. Let's define the structure of the notes.

```python
from enum import Enum
from typing import Optional, List

from beanie import Document
from pydantic import BaseModel


class TagColors(str, Enum):
    RED = "RED"
    BLUE = "BLUE"
    GREEN = "GREEN"


class Tag(BaseModel):
    name: str
    color: TagColors = TagColors.BLUE


class Note(Document):  # This is the document structure
    title: str
    text: Optional[str]
    tag_list: List[Tag] = []
```

A note consists of the required title, optional text, and a list of tags. Each tag has a name and a color. The
class `Note` has implemented all this in a pydantic way.

Now I will create the database connection and Beanie initialization:

```python
import motor.motor_asyncio
from beanie import init_beanie


async def main():
    # Create Motor client
    client = motor.motor_asyncio.AsyncIOMotorClient(
        f"mongodb://user:pass@host:27017/beanie_db",
        serverSelectionTimeoutMS=100
    )

    # Init Beanie
    await init_beanie(client.beanie_db, document_models=[Note])

```

No surprises here. Beanie uses Motor as an asynchronous driver for MongoDB. For initialization, I need to provide the
list of all Beanie documents that I will be working with.

## Web application

As API framework I will use the popular FastApi.

```python
from fastapi import FastAPI

app = FastAPI()
app.include_router(notes_router, prefix="/v1", tags=["notes"])
```

I will first implement a simple CRUD to show the basics of Beanie

### Create

Before any endpoint implementation, I would like to show how to create a document:

```python
note = Note(title="Monday", text="What a nice day!")
await note.create()
```

The `create` method stores the document in the database. Also, Beanie allows document insertion in a few other ways,
including batch insert. Examples of usage can be found in the `Document` method descriptions by
the [link](https://github.com/roman-right/beanie)

Now I'll demonstrate the same trick, but this time inside the endpoint:

```python
from fastapi import APIRouter

notes_router = APIRouter()


@notes_router.post("/notes/", response_model=Note)
async def create_note(note: Note):
    # Note creation
    await note.create()

    return note
```

{% details Click to see request details %}

POST `localhost:10001/v1/notes`

Input:

```json
{
  "title": "Monday",
  "text": "Is the best day ever!"
}
```

Output:

```json
{
  "_id": "60425951ded355386e0666ed",
  "title": "Monday",
  "text": "Is the best day ever!",
  "tag_list": []
}
```

{% enddetails %}

FastAPI uses Pydantic models to parse the request body. This means that I can use Beanie `Document` as the model and
then work with the already parsed document. To insert it into the database, I use the `create` method again.

### Read

In the response, it returns `_id` - the unique id of the document in the database. Now I'll show how to retrieve the
note based on its id.

**Independent implementation:**

```python
note = await Note.get(note_id)
```

**Inside the endpoint:**

```python
from beanie import PydanticObjectId


# Helper method to get instances
async def get_note(note_id: PydanticObjectId) -> Note:
    # Note retrieval
    note = await Note.get(note_id)

    if note is None:
        raise HTTPException(
            status_code=404,
            detail="Note not found"
        )
    return note


# Actual endpoint
@notes_router.get("/notes/{note_id}", response_model=Note)
async def get_note_by_id(
        # Helper usage with Depends annotation
        note: Note = Depends(get_note)
):
    return note
```

{% details Click to see request details %}

GET `localhost:10001/v1/notes/60425951ded355386e0666ed`

Output:

```json
{
  "_id": "60425951ded355386e0666ed",
  "title": "Monday",
  "text": "Is the best day ever!",
  "tag_list": []
}
```

{% enddetails %}

### Update

The application can already create and read the notes, but it can't do anything with the tags yet. That's what I'm going
to do next.

**Independent implementation:**

```python
tag = Tag(name="false", color="RED")
await note.update(
    update_query={"$push": {"tag_list": tag.dict()}}
)
```

**Inside the endpoint:**

```python
@notes_router.put("/notes/{note_id}/add_tag", response_model=Note)
async def add_tag(tag: Tag, note: Note = Depends(get_note)):
    # Update the note
    await note.update(
        update_query={"$push": {"tag_list": tag.dict()}}
    )

    return note
```

{% details Click to see request details %}

PUT `localhost:10001/v1/notes/60425951ded355386e0666ed/add_tag`

Input:

```json
{
  "name": "false",
  "color": "RED"
}
```

Output:

```json
{
  "_id": "60425951ded355386e0666ed",
  "title": "Monday",
  "text": "Is the best day ever!",
  "tag_list": [
    {
      "name": "false",
      "color": "RED"
    }
  ]
}
```

{% enddetails %}

There are two main types of Beanie `Document` update:

- replace - full update of the document
- update - partial update of the document

Replace is useful in many cases, but in the current one, I don't know if the `Note` document is in the actual state now.
Some tags might have been added after the last synchronization with the database. If I replace the document with new
data, I can easily lose some data. That's why I use the partial update here. As argument, the `update` method takes a
query in PyMongo query format.

### Delete

The delete operation is not that interesting to talk much about.

**Independent implementation:**

```python
await note.delete()
```

**Inside the endpoint:**

```python
@notes_router.delete("/notes/{note_id}", response_model=StatusModel)
async def get_note_by_id(note: Note = Depends(get_note)):
    # Delete the note
    await note.delete()

    return StatusModel(status=Statuses.DELETED)
```

{% details Click to see request details %}

DELETE `localhost:10001/v1/notes/60425951ded355386e0666ed`

Output:

```json
{
  "status": "DELETED"
}
```

{% enddetails %}

### Lists

CRUD is done, but no service gets around list endpoints. The implementation is simple again.

**Independent implementation:**

```python
all_notes = await Note.find_all().to_list()
red_notes = Note.find_many({"tag_list.color": "RED"}).to_list()
```

**Inside the endpoint:**

```python
@notes_router.get(
    "/notes/",
    response_model=List[Note]
)
async def get_all_notes():
    # Get all notes
    return await Note.find_all().to_list()


@notes_router.get(
    "/notes/by_tag/{tag_name}",
    response_model=List[Note]
)
async def filter_notes_by_tag(tag_name: str):
    # Filter notes
    return await Note.find_many(
        {"tag_list.name": tag_name}
    ).to_list()
```

{% details Click to see request details %}

GET `localhost:10001/v1/notes`

Output:

```json
[
  {
    "_id": "60425ac0ded355386e0666ee",
    "title": "Monday",
    "text": "Is the best day ever!",
    "tag_list": [
      {
        "name": "false",
        "color": "RED"
      }
    ]
  },
  {
    "_id": "60425adeded355386e0666ef",
    "title": "Monday",
    "text": "Is, probably, not the best day ever..",
    "tag_list": [
      {
        "name": "true",
        "color": "GREEN"
      }
    ]
  }
]
```

GET `localhost:10001/v1/notes/by_tag/true`

Output:

```json
[
  {
    "_id": "60425adeded355386e0666ef",
    "title": "Monday",
    "text": "Is, probably, not the best day ever..",
    "tag_list": [
      {
        "name": "true",
        "color": "GREEN"
      }
    ]
  }
]
```

{% enddetails %}

The `find_all` method tells everything about itself by name only. `find_many` is also simple. It takes PyMongo's query
as an argument to filter the documents.

### Aggregations

And finally, I want to show how to create aggregations with Beanie. In this example, I'll calculate how many notes I
have per tag name.

**Independent implementation:**

```python
class AggregationResponseItem(BaseModel):
    id: str = Field(None, alias="_id")
    total: int


results = await Note.aggregate(
    aggregation_query=[
        {"$unwind": "$tag_list"},
        {"$group": {
            "_id": "$tag_list.name",
            "total": {"$sum": 1}
        }}
    ],
    item_model=AggregationResponseItem
).to_list()
```

**Inside the endpoint:**

```python
@notes_router.get("/notes/aggregate/by_tag_name", response_model=List[AggregationResponseItem])
async def filter_notes_by_tag_name():
    # Notes aggregation
    return await Note.aggregate(
        aggregation_query=[
            {"$unwind": "$tag_list"},
            {"$group": {
                "_id": "$tag_list.name",
                "total": {"$sum": 1}
            }}
        ],
        item_model=AggregationResponseItem
    ).to_list()
```

{% details Click to see request details %}

GET `localhost:10001/v1/notes/aggregate/by_tag_name`

Output:

```json
[
  {
    "_id": "false",
    "total": 1
  },
  {
    "_id": "true",
    "total": 1
  }
]
```

{% enddetails %}

In all the examples before aggregation, the result of the `Note` methods were `Note` objects or lists of the `Note`
objects. But in the aggregation case, the result can have any structure. To continue work with the python objects I
provide parameter `item_model=AggregationResponseItem` to the `aggregate` method and it returns a list of
the `AggregationResponseItem` objects.

# Conclusion

Well, the service is done. I've shown how easy it is to do things with Beanie. You can stop thinking about parsing and
validating database data and just focus on your project. Certainly, I didn't use all the possible functions. You can
find the whole list of methods in the project description [here](https://github.com/roman-right/beanie)

Beanie has become a very important part of my development toolset. Especially when it comes to building prototypes. And
I'm happy to share it with the community. I continue to use it in my projects - which means I continue to develop it.
The next big thing I want to implement is structure and data migrations.

You are always welcome to participate in the development :-) Thank you very much for your time!

GitHub and PyPI project links:

- https://github.com/roman-right/beanie
- https://pypi.org/project/beanie/

Demo project from this article:

- https://github.com/roman-right/beanie-fastapi-demo