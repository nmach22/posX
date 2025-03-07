from typing import Any, Protocol

from fastapi import APIRouter, Depends, HTTPException
from fastapi.requests import Request
from pydantic import BaseModel

from app.core.classes.errors import DoesntExistError, AlreadyClosedError
from app.core.classes.receipt_service import ReceiptService
from app.core.Interfaces.product_interface import Product
from app.core.Interfaces.receipt_interface import (
    AddProductRequest,
)
from app.core.Interfaces.receipt_repository_interface import ReceiptRepositoryInterface
from app.core.Interfaces.repository import Repository
from app.infra.api.products import ErrorResponse


receipts_api = APIRouter()


class ReceiptProductDict(BaseModel):
    id: str
    quantity: int
    price_in_GEL: float
    total_in_GEL: float


class ReceiptEntry(BaseModel):
    id: str
    shift_id: str
    currency: str
    status: str
    products: list[ReceiptProductDict]
    total_in_GEL: float


class PaymentResponse(BaseModel):
    id: str
    total: float
    discounted_total: float
    reduced_price: float
    currency: str


class CreateReceiptRequest(BaseModel):
    shift_id: str
    currency: str


class ReceiptResponse(BaseModel):
    receipt: ReceiptEntry


class _Infra(Protocol):
    def receipts(self) -> ReceiptRepositoryInterface:
        pass

    def products(self) -> Repository[Product]:
        pass


def create_receipts_repository(request: Request) -> ReceiptRepositoryInterface:
    infra: _Infra = request.app.state.infra
    return infra.receipts()


def create_products_repository(request: Request) -> Repository[Product]:
    infra: _Infra = request.app.state.infra
    return infra.products()


@receipts_api.post(
    "",
    status_code=201,
    responses={
        404: {"model": ErrorResponse, "description": "Shift not found."},
        409: {"model": ErrorResponse, "description": "Shift already closed."},
    },
)
def create_receipt(
    request: CreateReceiptRequest,
    repository: ReceiptRepositoryInterface = Depends(create_receipts_repository),
) -> ReceiptResponse:
    receipt_service = ReceiptService(repository)
    try:
        created_receipt = receipt_service.create_receipt(
            request.shift_id, request.currency
        )
    except DoesntExistError:
        raise HTTPException(
            status_code=404,
            detail={"error": {"message": "Shift with this id does not exist."}},
        )
    except AlreadyClosedError:
        raise HTTPException(
            status_code=409,
            detail={
                "error": {
                    "message": f"Shift with id<{request.shift_id}> is already closed."
                }
            },
        )

    return ReceiptResponse(
        receipt=ReceiptEntry(
            id=created_receipt.id,
            shift_id=request.shift_id,
            currency=request.currency,
            status=created_receipt.status,
            products=[],
            total_in_GEL=created_receipt.total,
        )
    )


@receipts_api.post("/{receipt_id}/close")
def close_receipt(
    receipt_id: str,
    repository: ReceiptRepositoryInterface = Depends(create_receipts_repository),
) -> dict[Any, Any]:
    receipt_service = ReceiptService(repository)
    try:
        receipt_service.close_receipt(receipt_id)
        return {"message": f"Receipt {receipt_id} successfully closed."}
    except DoesntExistError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@receipts_api.post(
    "/{receipt_id}/products",
    status_code=201,
    responses={
        404: {"model": ErrorResponse, "description": "Product not found."},
        400: {"model": ErrorResponse, "description": "receipt already closed ."},
    },
)
def add_product(
    receipt_id: str,
    request: AddProductRequest,
    receipts_repo: ReceiptRepositoryInterface = Depends(create_receipts_repository),
) -> ReceiptResponse:
    receipt_service = ReceiptService(receipts_repo)

    try:
        receipt = receipt_service.add_product(receipt_id, request)
    except DoesntExistError:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {"message": "product or receipt with this id does not exist."}
            },
        )
    except AlreadyClosedError:
        raise HTTPException(
            status_code=400,
            detail={"error": {"message": f"receipt with this id already closed."}},
        )
    return get_receipt_response(receipt)


def get_receipt_response(receipt):
    return ReceiptResponse(
        receipt=ReceiptEntry(
            id=receipt.id,
            shift_id=receipt.shift_id,
            currency=receipt.currency,
            status=receipt.status,
            products=[
                ReceiptProductDict(
                    id=p.id,
                    quantity=p.quantity,
                    price_in_GEL=float(p.price / 100),
                    total_in_GEL=float(p.total / 100),
                )
                for p in receipt.products
            ],
            total_in_GEL=float(receipt.total / 100),
        )
    )


@receipts_api.get(
    "/{receipt_id}",
    responses={404: {"model": ErrorResponse, "description": "receipt not found."}},
)
def get_receipt(
    receipt_id: str,
    receipts_repo: ReceiptRepositoryInterface = Depends(create_receipts_repository),
) -> ReceiptResponse:
    receipt_service = ReceiptService(receipts_repo)
    try:
        receipt = receipt_service.read_receipt(receipt_id)
    except DoesntExistError:
        raise HTTPException(
            status_code=404,
            detail={"error": {"message": "receipt with this id does not exist."}},
        )
    return get_receipt_response(receipt)


@receipts_api.post(
    "/{receipt_id}/quotes",
    responses={404: {"model": ErrorResponse, "description": "Receipt not found."}},
)
def calculate_payment(
    receipt_id: str,
    receipts_repo: ReceiptRepositoryInterface = Depends(create_receipts_repository),
) -> PaymentResponse:
    receipt_service = ReceiptService(receipts_repo)

    # Call the repository method to calculate payment
    try:
        receipt_payment = receipt_service.calculate_payment(receipt_id)
    except DoesntExistError:
        raise HTTPException(
            status_code=404,
            detail={"error": {"message": "receipt with this id does not exist."}},
        )

    # return receipt_payment
    return PaymentResponse(
        id=receipt_payment.receipt.id,
        total=receipt_payment.receipt.total / 100,
        discounted_total=receipt_payment.discounted_price,
        reduced_price=receipt_payment.reduced_price,
        currency=receipt_payment.receipt.currency,
    )


@receipts_api.post(
    "/{receipt_id}/payments",
    responses={
        404: {"model": ErrorResponse, "description": "Receipt not found."},
        400: {"model": ErrorResponse, "description": "receipt already closed ."},
    },
)
def add_payment(
    receipt_id: str,
    receipts_repo: ReceiptRepositoryInterface = Depends(create_receipts_repository),
) -> PaymentResponse:
    receipt_service = ReceiptService(receipts_repo)
    try:
        receipt_payment = receipt_service.add_payment(receipt_id)
    except DoesntExistError:
        raise HTTPException(
            status_code=404,
            detail={"error": {"message": "receipt with this id does not exist."}},
        )
    except AlreadyClosedError:
        raise HTTPException(
            status_code=400,
            detail={"error": {"message": f"receipt with this id already closed."}},
        )

    return PaymentResponse(
        id=receipt_payment.receipt.id,
        total=receipt_payment.receipt.total / 100,
        discounted_total=receipt_payment.discounted_price,
        reduced_price=receipt_payment.reduced_price,
        currency=receipt_payment.receipt.currency,
    )
