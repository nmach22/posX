from typing import Protocol

from app.core.Interfaces.receipt_interface import (
    AddProductRequest,
    Receipt,
    ReceiptForPayment,
)


class ReceiptRepositoryInterface(Protocol):
    def create(self, item: Receipt) -> Receipt:
        pass

    def read(self, item_id: str) -> Receipt:
        pass

    def update(self, item_id: str) -> None:
        pass

    def add_product_to_receipt(
        self, receipt_id: str, product_request: AddProductRequest
    ) -> Receipt:
        pass

    def calculate_payment(
        self,
        receipt_id: str,
    ) -> ReceiptForPayment:
        pass
