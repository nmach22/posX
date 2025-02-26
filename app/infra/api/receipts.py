from typing import Protocol

from fastapi import APIRouter, Depends
from fastapi.requests import Request
from pydantic import BaseModel

from app.core.classes.receipt_service import ReceiptService
from app.core.Interfaces.product_repository_interface import ProductRepositoryInterface
from app.core.Interfaces.receipt_interface import (
    AddProductRequest,
    ReceiptStatus,
)
from app.core.Interfaces.receipt_repository_interface import ReceiptRepositoryInterface

receipts_api = APIRouter()


class ReceiptProductDict(BaseModel):
    id: str
    quantity: int
    price: int
    total: int


class ReceiptEntry(BaseModel):
    id: str
    status: ReceiptStatus
    products: list[ReceiptProductDict]
    total: int


class ReceiptResponse(BaseModel):
    receipt: ReceiptEntry


class _Infra(Protocol):
    def receipts(self) -> ReceiptRepositoryInterface:
        pass

    def products(self) -> ProductRepositoryInterface:
        pass


def create_receipts_repository(request: Request) -> ReceiptRepositoryInterface:
    infra: _Infra = request.app.state.infra
    return infra.receipts()


def create_products_repository(request: Request) -> ProductRepositoryInterface:
    infra: _Infra = request.app.state.infra
    return infra.products()


@receipts_api.post("", status_code=201, response_model=ReceiptResponse)
def create_receipt(
    repository: ReceiptRepositoryInterface = Depends(create_receipts_repository),
) -> ReceiptResponse:
    receipt_service = ReceiptService(repository)
    created_receipt = receipt_service.create_receipt()
    return ReceiptResponse(
        receipt=ReceiptEntry(
            id=created_receipt.id,
            status=created_receipt.status,
            products=[],
            total=created_receipt.total,
        )
    )


@receipts_api.post(
    "/{receipt_id}/products", status_code=201, response_model=ReceiptResponse
)
def add_product(
    receipt_id: str,
    request: AddProductRequest,
    receipts_repo: ReceiptRepositoryInterface = Depends(create_receipts_repository),
) -> ReceiptResponse:
    receipt_service = ReceiptService(receipts_repo)

    receipt = receipt_service.add_product(receipt_id, request)
    return ReceiptResponse(
        receipt=ReceiptEntry(
            id=receipt.id,
            status=receipt.status,
            products=[
                ReceiptProductDict(
                    id=p.id, quantity=p.quantity, price=p.price, total=p.total
                )
                for p in receipt.products
            ],
            total=receipt.total,
        )
    )
