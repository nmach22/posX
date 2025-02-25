from copy import deepcopy
from dataclasses import dataclass

from app.core.Interfaces.product_interface import Product
from app.core.Interfaces.receipt_interface import (
    AddProductRequest,
    Receipt,
    ReceiptProduct,
)
from app.core.Interfaces.receipt_repository_interface import ReceiptRepositoryInterface


@dataclass
class ReceiptInMemoryRepository(ReceiptRepositoryInterface):
    receipts: list[Receipt]
    products: list[Product]

    def add_receipt(self, receipt: Receipt) -> Receipt:
        self.receipts.append(deepcopy(receipt))
        return receipt

    def close_receipt(self, receipt_id: str) -> None:
        for receipt in self.receipts:
            if receipt.id == receipt_id:
                receipt.status = "closed"
                break

    def get_receipt(self, receipt_id: str) -> Receipt:
        for receipt in self.receipts:
            if receipt.id == receipt_id:
                return receipt

    def add_product_to_receipt(self, receipt_id: str, product_request: AddProductRequest) -> Receipt:
        product_price = 0
        for product in self.products:
            if product.id == product_request.product_id:
                product_price = product.price
        for receipt in self.receipts:
            if receipt.id == receipt_id:
                total_price = product_request.quantity * product_price

                product = ReceiptProduct(
                    id=product_request.product_id,
                    quantity=product_request.quantity,
                    price=product_price,
                    total=total_price
                )

                receipt.products.append(product)
                receipt.total += total_price

                return receipt
        raise ValueError("Receipt not found")
