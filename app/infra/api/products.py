from typing import Any, Dict, Protocol

from fastapi import APIRouter, Depends, HTTPException
from fastapi.requests import Request
from pydantic import BaseModel

from app.core.classes.product_service import ProductService
from app.core.Interfaces.product_interface import Product, ProductRequest
from app.core.Interfaces.repository import Repository
from app.infra.in_memory_repositories.product_in_memory_repository import (
    DoesntExistError,
    ExistsError,
)

products_api = APIRouter()


class _Infra(Protocol):
    def products(self) -> Repository[Product]:
        pass


def create_products_repository(request: Request) -> Repository[Product]:
    infra: _Infra = request.app.state.infra
    return infra.products()


class ProductResponse(BaseModel):
    product: Product


class ProductsListResponse(BaseModel):
    products: list[Product]


class UpdateProductRequest(BaseModel):
    price: int


class ErrorResponse(BaseModel):
    error: Dict[str, str]  # Explicitly define Dict type


@products_api.post(
    "",
    status_code=201,
    responses={
        409: {
            "model": ErrorResponse,
            "description": "Product with the given barcode already exists.",
        }
    },
)
def create_product(
    request: ProductRequest,
    repository: Repository[Product] = Depends(create_products_repository),
) -> ProductResponse:
    product_service = ProductService(repository)

    try:
        created_product = product_service.create_product(request)
        return ProductResponse(product=created_product)
    except ExistsError:
        raise HTTPException(
            status_code=409,
            detail={
                "error": {
                    "message": f"Product with barcode<{request.barcode}> already exists."
                }
            },
        )


@products_api.get("", status_code=200, response_model=ProductsListResponse)
def get_all_products(
    repository: Repository[Product] = Depends(create_products_repository),
) -> ProductsListResponse:
    product_service = ProductService(repository)
    products = product_service.read_all_products()

    return ProductsListResponse(
        products=[
            Product(
                id=_product.id,
                name=_product.name,
                barcode=_product.barcode,
                price=_product.price,
            )
            for _product in products
        ]
    )


@products_api.patch(
    "/{product_id}",
    status_code=200,
    responses={404: {"model": ErrorResponse, "description": "Product not found."}},
)
def update_product(
    product_id: str,
    request: UpdateProductRequest,
    repository: Repository[Product] = Depends(create_products_repository),
) -> dict[Any, Any]:
    product_service = ProductService(repository)

    try:
        existing_product = product_service.get_product(product_id)
    except DoesntExistError:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {"message": f"product with id<{product_id}> does not exist."}
            },
        )

    updated_product = Product(
        id=existing_product.id,
        name=existing_product.name,
        barcode=existing_product.barcode,
        price=request.price,
    )
    try:
        product_service.update_product_price(updated_product)
    except DoesntExistError:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {"message": f"product with id<{product_id}> does not exist."}
            },
        )

    return {}
