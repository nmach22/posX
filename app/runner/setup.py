from fastapi import FastAPI

from app.infra.api.products import products_api
from app.infra.api.receipts import receipts_api
from app.infra.in_memory import InMemory


def setup() -> FastAPI:
    app = FastAPI()

    app.state.infra = InMemory()
    app.include_router(products_api, prefix="/products", tags=["products"])
    app.include_router(receipts_api, prefix="/receipts", tags=["receipts"])

    return app
