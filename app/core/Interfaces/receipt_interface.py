from typing import Protocol

from app.core.Interfaces.product_interface import Product


class ReceiptInterface(Protocol):

    def add_product(self, product: Product) -> None:
        pass
