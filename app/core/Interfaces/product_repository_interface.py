from typing import Protocol

from app.core.Interfaces.product_interface import Product


class ProductRepositoryInterface(Protocol):
    def add_product(self, product: Product) -> None:
        pass
    def get_product(self, product_id: str) -> Product:
        pass
    def update_product(self, new_price: int, product_id: str) -> None:
        pass
    def read_all_products(self) -> list[Product]:
        pass