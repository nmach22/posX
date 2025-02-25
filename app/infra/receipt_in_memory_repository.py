from copy import deepcopy
from dataclasses import dataclass

from app.core.Interfaces.receipt_interface import (
    AddProductRequest,
    Receipt,
    ReceiptProduct,
)


@dataclass
class ReceiptInMemoryRepository:
    receipts: list[Receipt]

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
        for receipt in self.receipts:
            if receipt.id == receipt_id:
                # todo: change this??
                price = 10.0
                total_price = product_request.quantity * price


                product = ReceiptProduct(
                    id=product_request.product_id,
                    quantity=product_request.quantity,
                    price=price,
                    total=total_price
                )


                receipt.products.append(product)
                receipt.total += total_price

                return receipt
        raise ValueError("Receipt not found")
