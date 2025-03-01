from typing import Protocol

from app.core.Interfaces.product_interface import Product


class ProductRepositoryInterface(Protocol):
    def create(self, product: Product) -> Product:
        pass

    def read(self, product_id: str) -> Product:
        pass

    def update(self, product: Product) -> None:
        pass

    def read_all(self) -> list[Product]:
        pass
