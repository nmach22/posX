from dataclasses import dataclass
from typing import Protocol


@dataclass
class ReceiptProduct:
    id: str
    quantity: int
    price: float
    total: float


@dataclass
class Receipt:
    id: str
    products: list[ReceiptProduct]
    status: str
    total: int


@dataclass
class AddProductRequest:
    product_id: str
    quantity: int

class ReceiptInterface(Protocol):

    def create_receipt(self)-> Receipt:
        pass

    def add_product(self, receipt_id: str, product_request: AddProductRequest) -> Receipt:
        pass

    def read_receipt(self, receipt_id: str) -> Receipt:
        pass

    def close_receipt(self, receipt_id: str) -> None:
        pass



