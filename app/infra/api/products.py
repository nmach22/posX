import uuid
from itertools import product
from typing import Protocol, Any

from fastapi import APIRouter, Depends
from fastapi.requests import Request
from pydantic import BaseModel

from app.core.Interfaces.product_interface import Product, ProductRequest
from app.core.Interfaces.product_repository_interface import ProductRepositoryInterface
from app.core.classes.product_service import ProductService
from app.infra.in_memory import InMemory

products_api = APIRouter()


class _Infra(Protocol):
    def products(self) -> ProductRepositoryInterface:
        pass


def create_products_repository(request: Request) -> ProductRepositoryInterface:
    # infra: _Infra = request.app.state.infra
    infra: _Infra = InMemory()
    return infra.products()


class ProductResponse(BaseModel):
    product: Product


class ProductsListResponse(BaseModel):
    products: list[Product]


class UpdateProductRequest(BaseModel):
    price: int


@products_api.post("", status_code=201, response_model=ProductResponse)
def create_product(
    request: ProductRequest,
    repository: ProductRepositoryInterface = Depends(create_products_repository),
) -> ProductResponse:
    product_service = ProductService(repository)
    created_product = product_service.create_product(request)

    return ProductResponse(product=created_product)


@products_api.get("", status_code=200, response_model=ProductsListResponse)
def get_all_products(
    repository: ProductRepositoryInterface = Depends(create_products_repository),
) -> ProductsListResponse:
    products = repository.read_all_products()

    return ProductsListResponse(
        products=[
            Product(
                id=product.id,
                name=product.name,
                barcode=product.barcode,
                price=product.price,
            )
            for product in products
        ]
    )


@products_api.patch("/{product_id}")
def update_product(
    product_id: str,
    request: UpdateProductRequest,
    repository: ProductRepositoryInterface = Depends(create_products_repository),
) -> dict[Any, Any]:
    # First read the existing product
    existing_product = repository.get_product(product_id)
    # Update only the price
    updated_product = Product(
        id=existing_product.id,
        name=existing_product.name,
        barcode=existing_product.barcode,
        price=request.price,
    )
    repository.update_product(updated_product)
    return {}
