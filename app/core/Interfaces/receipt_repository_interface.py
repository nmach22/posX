from typing import Protocol

from app.core.Interfaces.receipt_interface import (
    AddProductRequest,
    Receipt,
    ReceiptForPayment,
)


class ReceiptRepositoryInterface(Protocol):
    def add_receipt(self, receipt: Receipt) -> Receipt:
        pass

    def close_receipt(self, receipt_id: str) -> None:
        pass

    def get_receipt(self, receipt_id: str) -> Receipt:
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
