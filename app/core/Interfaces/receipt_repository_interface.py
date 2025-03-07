from typing import Protocol

from app.core.Interfaces.campaign_interface import Campaign
from app.core.Interfaces.receipt_interface import (
    AddProductRequest,
    Receipt,
    ReceiptForPayment,
)
from app.core.Interfaces.repository import Repository


class ReceiptOperations(Protocol):
    def add_product_to_receipt(
        self, receipt_id: str, product_request: AddProductRequest
    ) -> Receipt:
        pass

    def calculate_payment(
        self,
        receipt_id: str,
    ) -> ReceiptForPayment:
        pass

    def add_payment(
        self,
        receipt_id: str,
    ) -> ReceiptForPayment:
        pass

    def get_other_products_with_same_campaign(self, campaign_id: str) -> list[str]:
        pass

    def product_not_in_receipt(self, product_id: str, receipt_id: str) -> bool:
        pass

    def get_campaign_with_campaign_id(self, campaign_id: str) -> Campaign | None:
        pass


class ReceiptRepositoryInterface(Repository[Receipt], ReceiptOperations, Protocol):
    pass
