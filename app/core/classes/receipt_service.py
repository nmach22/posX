import uuid
from dataclasses import dataclass

from app.core.Interfaces.receipt_interface import (
    AddProductRequest,
    Receipt,
    ReceiptInterface,
    ReceiptForPayment,
)
from app.core.Interfaces.receipt_repository_interface import ReceiptRepositoryInterface


@dataclass
class ReceiptService(ReceiptInterface):
    repository: ReceiptRepositoryInterface

    def create_receipt(self) -> Receipt:
        receipt_id = uuid.uuid4()
        products = []
        status = "open"
        total = 0
        receipt = Receipt(
            id=str(receipt_id), products=products, status=status, total=total
        )
        self.repository.add_receipt(receipt)
        return receipt

    def read_receipt(self, receipt_id: str) -> Receipt:
        return self.repository.get_receipt(receipt_id)

    def close_receipt(self, receipt_id: str) -> None:
        self.repository.close_receipt(receipt_id)

    def add_product(
        self, receipt_id: str, product_request: AddProductRequest
    ) -> Receipt:
        return self.repository.add_product_to_receipt(receipt_id, product_request)

    def calculate_payment(self, receipt_id: str) -> ReceiptForPayment:
        return self.repository.calculate_payment(receipt_id)
