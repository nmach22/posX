from dataclasses import dataclass
from typing import Protocol

from pydantic import BaseModel


@dataclass
class Product:
    id: str
    name: str
    price: int
    barcode: str


@dataclass
class ProductRequest:
    name: str
    price: int
    barcode: str


class ProductInterface(Protocol):
    def create_product(self, product_request: ProductRequest) -> Product:
        pass

    def read_all_products(self) -> list[Product]:
        pass

    def update_product_price(self, product: Product) -> None:
        pass

    def get_product(self, product_id: str) -> Product:
        pass
