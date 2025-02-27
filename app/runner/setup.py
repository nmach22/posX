from fastapi import FastAPI

from app.infra.api.campaigns import campaigns_api
from app.infra.api.products import products_api
from app.infra.api.receipts import receipts_api
from app.infra.api.shifts import shifts_api
from app.infra.in_memory import InMemory


def setup() -> FastAPI:
    app = FastAPI()

    app.state.infra = InMemory()
    app.include_router(products_api, prefix="/products", tags=["products"])
    app.include_router(receipts_api, prefix="/receipts", tags=["receipts"])
    app.include_router(campaigns_api, prefix="/campaigns", tags=["campaigns"])
    app.include_router(shifts_api, prefix="/shifts", tags=["shifts"])

    return app
