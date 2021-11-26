# Beanie FastAPI Demo

This is an example project demonstrating the use of [Beanie ODM](https://github.com/roman-right/beanie) in a 
[FastAPI](https://fastapi.tiangolo.com) application

# Setup

This demo is based on python3 and uses [Poetry](https://python-poetry.org/docs/) to manage dependencies. Make sure you 
have installed poetry using the [installation instructions](https://python-poetry.org/docs/#installation) before you 
begin.

As beanie is an ODM for [MongoDB](https://www.mongodb.com) it needs a MongoDB database to run. If you already
have a Mongo database running, change the settings in `beanie_fastapi_demo/main.py` accordingly. In other cases
it is recommended to run MongoDB using **[docker](https://docs.docker.com/engine/install/)** and 
**[docker-compose](https://docs.docker.com/compose/install/)**.

## Install the requirements

Installing the requirements using poetry is easy, just run the command below
```shell
poetry install
```

## Run MongoDB

To run MongoDB using docker-compose, run
```shell
docker-compose -f docker-compose-mongodb.yml up -d
```

## Start the app

To activate the environment managed by poetry and run the application, run
```shell
poetry shell
python3 beanie-fastapi-demo/main.py
```
The demo application can now be reached on http://127.0.0.1:10001/

### Interactive API Docs

If you go to http://127.0.0.1:10001/docs you will see the automatic interactive API documentation generated with 
[Swagger UI](https://github.com/swagger-api/swagger-ui)

Alternatively you can go to http://127.0.0.1/redoc see the automatic interactive API documentation generated with
[Redoc](https://github.com/Rebilly/ReDoc)

# Links

* **Beanie**: https://github.com/roman-right/beanie
* **FastAPI**: https://fastapi.tiangolo.com

## Other example projects

* **fastapi-cosmos-beanie**: https://github.com/tonybaloney/ants-azure-demos/tree/master/fastapi-cosmos-beanie
* **fastapi-beanie-jwt**: https://github.com/flyinactor91/fastapi-beanie-jwt
