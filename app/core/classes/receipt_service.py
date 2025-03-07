import uuid
from dataclasses import dataclass

from app.core.classes.errors import AlreadyClosedError
from app.core.Interfaces.receipt_interface import (
    AddProductRequest,
    Receipt,
    ReceiptForPayment,
    ReceiptInterface,
    ReceiptProduct,
)
from app.core.Interfaces.receipt_repository_interface import ReceiptRepositoryInterface


@dataclass
class ReceiptService(ReceiptInterface):
    repository: ReceiptRepositoryInterface

    def create_receipt(self, shift_id: str, currency: str) -> Receipt:
        receipt_id = uuid.uuid4()
        products: list[ReceiptProduct] = []
        status = "open"
        total = 0
        total_payment = 0
        receipt = Receipt(
            id=str(receipt_id),
            shift_id=shift_id,
            currency=currency,
            status=status,
            products=products,
            total=total,
            discounted_total=total_payment,
        )
        self.repository.create(receipt)
        return receipt

    def read_receipt(self, receipt_id: str) -> Receipt:
        return self.repository.read(receipt_id)

    def close_receipt(self, receipt_id: str) -> None:
        receipt = self.read_receipt(receipt_id)
        if receipt.status == "closed":
            raise AlreadyClosedError(f"Receipt with ID {receipt.id} is already closed.")
        receipt.status = "closed"
        self.repository.update(receipt)

    def add_product(
        self, receipt_id: str, product_request: AddProductRequest
    ) -> Receipt:
        return self.repository.add_product_to_receipt(receipt_id, product_request)

    def calculate_payment(self, receipt_id: str) -> ReceiptForPayment:
        return self.repository.calculate_payment(receipt_id)

    def add_payment(self, receipt_id: str) -> ReceiptForPayment:
        self.close_receipt(receipt_id)
        return self.repository.add_payment(receipt_id)
