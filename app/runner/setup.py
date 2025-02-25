from fastapi import FastAPI

from app.infra import api
from app.infra.api.products import products_api
from app.infra.in_memory import InMemory


def setup() -> FastAPI:
    app = FastAPI()

    api.state.infra = InMemory()
    app.include_router(products_api, prefix="/products", tags=["products"])

    return app
