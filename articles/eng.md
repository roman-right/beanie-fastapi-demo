I'm excited to introduce [Beanie](https://github.com/roman-right/beanie) - micro ORM for MongoDB!


The main Beanie component is [Pydantic](https://pydantic-docs.helpmanual.io/) - a popular library for data parsing and validation. It helps to implement the main feature - data structuredness. Beanie Document - is an abstraction over the Pydantic BaseModel, which allows working with python objects on the application level and JSON objects on the database level. In general case one MongoDB collection is associated with only one Beanie Document. This is appending predictability in work with the database, and, at the same time, it keeps the whole flexibility of the MongoDB documents - it is possible to represent any data structure with Pydantic model (or even a group of structures with Optional and Union annotations).

I make quite a bit of pet-projects: experiments with the new technologies and proofs of concepts. For these purposes, I needed a tool to work with the database, which I could start using right out of the box without a long setup. And with which I could frequently change the data structure, add and drop elements here and there. This is how Beanie was born.

# Example

But this is boring a little, right? Let's move to the interesting part - the usage examples. It will show, how handy this tool is. 
I deliberately will skip some extra import and helpers here to not overload the picture and to keep the focus on the important things only. The whole working app from this article is in my GitHub repo [beanie-fastapi-demo](https://github.com/roman-right/beanie-fastapi-demo).

As an example, I will make a small rest-service for the notes management. 

## Installation

```
pip install beanie
```

OR

```
poetry add beanie
```

## Data model

The package is installed. Now I can start. Let's define the structure of notes.


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


class Note(Document):  # This is our ORM Document structure
    title: str
    text: Optional[str]
    tag_list: List[Tag] = []
```

A note consists of the required title, optional text, and a list of tags. Each tag has a name and color. Class `Note` has this all implemented in a Pydantic way.

Now I will create the database connection and Beanie initialization:

```python
import motor.motor_asyncio
from beanie.general import init_beanie


# CREATE MOTOR CLIENT
client = motor.motor_asyncio.AsyncIOMotorClient(
    f"mongodb://user:pass@host:27017/beanie_db",
    serverSelectionTimeoutMS=100
)

# INIT BEANIE
init_beanie(client.beanie_db, document_models=[Note])
```

There are no surprises here. Beanie uses Motor as an async driver for MongoDB. For the initialization, I have to provide the list of all Beanie documents, which I will work with.

As an API framework, I will use popular FastApi.

```python
from fastapi import FastAPI


app = FastAPI()
app.include_router(notes_router, prefix="/v1", tags=["notes"])
```

## Endpoints

I'll implement a simple CRUD firstly, to show the Beanie basics 

Note creation without endpoint:

```python
note = Note(title="Monday", text="What a nice day!")
await note.create()
```

### Create

Method `create` saves the document to the database. Also, Beanie allows inserting the documents in some other ways, including batch insert. Example of usage you can find in the Document's methods descriptions [by link](https://github.com/roman-right/beanie)

Now I'll demonstrate the same trick but with the endpoint this time:

```python
from fastapi import APIRouter

notes_router = APIRouter()


@notes_router.post("/notes/", response_model=Note)
async def create_note(note: Note):
    await note.create()
    return note
```

<details>
  <summary>Click to see request details</summary>
  
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
  
</details>

FastAPI uses Pydantic models for request body parsing. It means that as a model I can use Beanie Document and then work with the already parsed document. To insert it into the database I use the `create` method again.

### Read

In the response, it returns `_id` - unique id of the document in the database. Now I'll show, how to get the note by its id.

```python
from beanie.fields import PydanticObjectId


async def get_note(note_id: PydanticObjectId) -> Note:
    note = await Note.get(note_id)
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    return note

@notes_router.get("/notes/{note_id}", response_model=Note)
async def get_note_by_id(note: Note = Depends(get_note)):
    return note
```

<details>
  <summary>Click to see request details</summary>
  
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
  
</details>

### Update

The application already can create and read the notes, but still can not do anything with tags. This is what I'll do next:

```python
@notes_router.put("/notes/{note_id}/add_tag", response_model=Note)
async def add_tag(tag: Tag, note: Note = Depends(get_note)):
    await note.update(update_query={"$push": {"tag_list": tag.dict()}})
    return note
```

<details>
  <summary>Click to see request details</summary>
  
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
  
</details>

There are two main types of the Beanie Document update: 
replace - full document update
update - partial update of the document
Replace is useful in many cases, but in the current one, I don't know if the `Note` document is in the actual state now. Some tags could be added after the last synchronization with the database. If I'll replace the document with new data I easily can lose some data. That's why I use partial update here. As the argument `update` method uses query in the PyMongo query format.

### Delete

The deletion operation is not that interesting, to talk about it much:

```python
@notes_router.delete("/notes/{note_id}", response_model=StatusModel)
async def get_note_by_id(note: Note = Depends(get_note)):
    await note.delete()
    return StatusModel(status=Statuses.DELETED)
```

<details>
  <summary>Click to see request details</summary>
  
DELETE `localhost:10001/v1/notes/60425951ded355386e0666ed`
  

Output:

```json
{
    "status": "DELETED"
}
```
  
</details>

### Lists

CRUD is done, but no one service can avoid lists endpoints. The implementation of this is simple too:

```python
@notes_router.get("/notes/", response_model=List[Note])
async def get_all_notes():
    return await Note.find_all().to_list()


@notes_router.get("/notes/by_tag/{tag_name}", response_model=List[Note])
async def filter_notes_by_tag(tag_name: str):
    return await Note.find_many({"tag_list.name": tag_name}).to_list()
```

<details>
  <summary>Click to see request details</summary>
  
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

  
</details>

`find_all` method tells everything about self just with the name. `find_many` is simple too. It uses PyMongo's query as the argument to filter the documents.

### Aggregations

And finally, I want to show, how to make aggregations with Beanie. In this example, I'll calculate how many notes I have per tag name.

```python
class AggregationResponseItem(BaseModel):
    id: str = Field(None, alias="_id")
    total: int


@notes_router.get("/notes/aggregate/by_tag_name", response_model=List[AggregationResponseItem])
async def filter_notes_by_tag_name():
    return await Note.aggregate(
        aggregation_query=[
            {"$unwind": "$tag_list"},
            {"$group": {"_id": "$tag_list.name", "total": {"$sum": 1}}}
        ],
        item_model=AggregationResponseItem
    ).to_list()
```

<details>
  <summary>Click to see request details</summary>
  
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

</details>

In all the examples before aggregation, the result of the `Note` methods were `Note` objects or lists of the `Note` objects. But in the aggregation case, the result can have any structure. To continue work with the python objects I provide parameter `item_model=AggregationResponseItem` to the `aggregate` method and it returns a list of the `AggregationResponseItem` objects. 

# Conclusion

Well, the service is ready. I showed how simple it is to make things with Beanie. You can stop thinking about parsing and validating the database data and just focus on your project. For sure I didn't use all the possible features. The whole list of the methods you can find in the project description [here](https://github.com/roman-right/beanie)

Beanie is a really important thing in my development toolset now. Especially if we are talking about the prototype building. And I'm happy to share it with the community. I continue to use it in my projects - it means I'll develop it further. The next big thing I want to implement is the structure and data migrations.

You are always welcome to join the development :-) 
Thank you for your time!

GitHub and PyPI project links:
- https://github.com/roman-right/beanie
- https://pypi.org/project/beanie/

Demo project from this article:
- https://github.com/roman-right/beanie-fastapi-demo
