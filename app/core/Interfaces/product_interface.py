from dataclasses import dataclass
from typing import Protocol


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

    def create_product (self, product_request: ProductRequest) -> Product:
        pass

    def read_all_products (self, product_id: str) -> list[Product]:
        pass

    def update_product_price (self, new_price: int, product_id: str) -> None:
        pass

    def get_product(self, product_id: str) -> Product:
        pass


