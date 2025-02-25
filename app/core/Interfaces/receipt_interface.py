from dataclasses import dataclass
from typing import Protocol

from app.core.Interfaces.product_interface import Product


@dataclass
class Receipt:
    id: str
    products: list[Product]
    status: str
    total: int

class ReceiptInterface(Protocol):

    def create_receipt(self)-> Receipt:
        pass

    def add_product(self, product_id: str) -> Receipt:
        pass

    def close_receipt(self) -> None:
        pass



