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
    currency: str
    products: list[ReceiptProduct]
    status: str
    total: float
    discounted_total: float


@dataclass
class AddProductRequest:
    product_id: str
    quantity: int


@dataclass
class ReceiptForPayment:
    receipt: Receipt
    # girda 100, girs 90-discounted =90. reduced = 10
    discounted_price: float
    reduced_price: float


class ReceiptInterface(Protocol):
    def create_receipt(self, shift_id: str, currency: str) -> Receipt:
        pass

    def add_product(
        self, receipt_id: str, product_request: AddProductRequest
    ) -> Receipt:
        pass

    def read_receipt(self, receipt_id: str) -> Receipt:
        pass

    def close_receipt(self, receipt_id: str) -> None:
        pass

    def calculate_payment(self, receipt_id: str) -> ReceiptForPayment:
        pass
