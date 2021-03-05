

Beanie - микро ORM для MongoDB. 

Основным компонентом Beanie является Pydantic - популярная библиотека для парсинга и валидации данных. Благодаря этому реализована основная фишка - структурированность данных с сохранением гибкости. Документы Beanie - это абстракции над моделями Pydantic, которые позволяют работать с объектами питона на уровне приложения и JSON-ами на уровне базы данных. В общем случае с одной коллекцией монго связана лишь одна структура документа Beanie. Это добавляет предсказуемости при работе за базой данных и в то же время сохраняет всю гибкость документов монгодб - благодаря опшенал и унион аннотациям можно представить любую, даже самую разветвлённую структуру.

Я пишу довольно много пет-проектов, эксперементирую с теми или иными технологиями или проверяю идеи. В качестве базы в таких случаях я обычно использую Монго из-за её документарности. Для этого мне нужен был инструмент, с которым можно прямо из коробки набросать структуру данных и начать с ней работать, периодчески изменяя схемы, добаляя или удаляя компоненты. Так и родилась Beanie. 

Но это всё слова. Давайте передём к интересному - примерам использования. Они смогут показать, какой это удобный инструмент.

Я намеренно убираю из кода в статье  многие импорты и хелперы, чтобы не перегружать листинги и не отвлекать читающего. Полный работающий пример лежит в моём гитхаб-репозитории [beanie-fastapi-demo](https://github.com/roman-right/beanie-fastapi-demo).

В качестве примера я хочу написать небольшой веб-сервис для работы с заметками.

Для начала определимся со структурой заметок:

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

Заметка состоит из обязательного заголовка, необязательного текста и списка тегов, каждый из котрых имеет название и цвет. Это всё, как вы можете заметить, очень удобно описывается аннотациями при создании Beanie документа Note.

Теперь нужно создать подключение к базе и проинициализировать Beanie:

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

Здесь всё без сюрпризова. Beanie использует Motor в качестве асинхронного драйвера MongoDB. Для инициализации требуется передать список всех Документов, с которыми мы работаем.

В качестве апи-фреймворка я буду использовать популярный сейчас FastAPI. Создание приложения и подключения роутеров не касается темы этйо статьи - я просто оставлю их здесь.

```python
from fastapi import FastAPI


app = FastAPI()
app.include_router(notes_router, prefix="/v1", tags=["notes"])
```

Эндпойнты. Первым делом я реализую простой CRUD, чтобы показать самые основы работы с Beanie.

Создание заметки без эндпойнта:
```python
note = Note(title="Monday", text="What a nice day!")
await note.create()
```
Метод create() создаёт документ в базе данных. Так же в Beanie есть возможность создавать документы в базе иными способами, включая множественный инсерт. Примеры использования можно найти в перечислении методов документа [по ссылке](https://github.com/roman-right/beanie)

Теперь я проверну этот же фокус, но уже внутри эндпойнта:
```python
from fastapi import APIRouter

notes_router = APIRouter()


@notes_router.post("/notes/", response_model=Note)
async def create_note(note: Note):
    await note.create()
    return note
```

<details>
  <summary>Пример запроса:</summary>
  
POST `localhost:10001/v1/notes`
  
Вход:
  
```json
{
  "title": "Test title 2",
  "text": "test text"
}
```

Выход:

```json
{
    "_id": "6041fc953765e1290b819f3d",
    "title": "Test title 2",
    "text": "test text",
    "tag_list": []
}
```
  
</details>

FastAPI использует модели Pydantic для парсинга данных из тела запроса. Это значит, что в качестве модели для парсинга можно так же использовать и документы Beanie и затем работать с документом с уже заполненными полями. Для создания документа в базе так же используется метод create().

В предыдущем запросе вместе с полями заметки нам возвращался её уникальный идентификатор в бае данных. Сейчас я реализую метод получения заметки по её идентификатору.

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

Получение документа реализовано методом get(), который возвращает документ или None в зависимости от того, присутсвует ли документ с таким id в базе. 

Приложение уже может создавать заметки и читать их, но ещё не было реализовано использования тэгов. Сейчас я это исправлю.

```python
@notes_router.put("/notes/{note_id}/add_tag", response_model=Note)
async def add_tag(tag: Tag, note: Note = Depends(get_note)):
    await note.update(update_query={"$push": {"tag_list": tag.dict()}})
    return note
```

Обновление документа в Beanie возможно двумя основными способами - `replace` - полная перезапись документа и `update` - частичное его обновление. `replace` удобен во многих случаях, но в данной ситуации нужно добавить тэг в список тэгов и я не знаю, находится ли документ в данный момент в актуальном состоянии. Он мог быть изменён уже после того, как был запрошен в этом эндпойнте. Вот почему здесь используется частичное обновление. В качестве аргумента метода `update` используется запрос в PyMongo-формате.

Удаление не требует отдельного рассмотрения
```python
@notes_router.delete("/notes/{note_id}", response_model=StatusModel)
async def get_note_by_id(note: Note = Depends(get_note)):
    await note.delete()
    return StatusModel(status=Statuses.DELETED)
```

Следующая группа эндпойнтов - получение списков.
```python
@notes_router.get("/notes/", response_model=List[Note])
async def get_all_notes():
    return await Note.find_all().to_list()


@notes_router.get("/notes/by_tag/{tag_name}", response_model=List[Note])
async def filter_notes_by_tag(tag_name: str):
    return await Note.find_many({"tag_list.name": tag_name}).to_list()
```

`find_all` метод рассказывает о себе всё одним лишь своим названием. В качестве аргумента для метода `find_many` используется запрос так же в PyMongo-формате

И заключительная группа - аггрегации.
В качестве примера рассмотрим получения количества заметок по названию тэга.

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

Во всех предыдущих примерах результатом работы методов класса `Note` были или объекты этого класса, или списки таких объектов. Но в случае с аггрегацией1 результатом может, и скорее всего будет - это зависит от Вас, совершенно другая структура данных. Чтобы продолжить работать с объектами питона я передаю в метод `aggregate` параметр `item_model=AggregationResponseItem` и на выходе получаю список обхектов класса `AggregationResponseItem`. 

