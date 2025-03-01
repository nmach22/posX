from typing import Protocol

from app.core.Interfaces.receipt_interface import (
    AddProductRequest,
    Receipt,
    ReceiptForPayment,
)
from app.core.Interfaces.repository import Repository


class ReceiptRepositoryInterface(Repository[Receipt], Protocol):
    def add_product_to_receipt(
        self, receipt_id: str, product_request: AddProductRequest
    ) -> Receipt:
        pass

    def calculate_payment(
        self,
        receipt_id: str,
    ) -> ReceiptForPayment:
        pass
