from dataclasses import dataclass
from enum import Enum
from typing import Protocol


class ReceiptStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"


@dataclass
class ReceiptProduct:
    id: str
    quantity: int
    price: int
    total: int


@dataclass
class Receipt:
    id: str
    shift_id: str
    products: list[ReceiptProduct]
    status: str
    total: int


@dataclass
class AddProductRequest:
    product_id: str
    quantity: int


class ReceiptInterface(Protocol):
    def create_receipt(self) -> Receipt:
        pass

    def add_product(
        self, receipt_id: str, product_request: AddProductRequest
    ) -> Receipt:
        pass

    def read_receipt(self, receipt_id: str) -> Receipt:
        pass

    def close_receipt(self, receipt_id: str) -> None:
        pass
