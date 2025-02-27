from copy import deepcopy
from dataclasses import dataclass, field
from app.core.Interfaces.receipt_interface import (
    AddProductRequest,
    Receipt,
    ReceiptProduct,
    ReceiptForPayment,
)
from app.core.Interfaces.receipt_repository_interface import ReceiptRepositoryInterface
from app.infra.product_in_memory_repository import (
    DoesntExistError,
    ExistsError,
    ProductInMemoryRepository,
)
from app.infra.shift_in_memory_repository import ShiftInMemoryRepository


@dataclass
class ReceiptInMemoryRepository(ReceiptRepositoryInterface):
    receipts: list[Receipt] = field(default_factory=list)
    products: ProductInMemoryRepository = field(
        default_factory=ProductInMemoryRepository
    )

    shifts: ShiftInMemoryRepository = field(default_factory=ShiftInMemoryRepository)

    def add_receipt(self, receipt: Receipt) -> Receipt:
        if any(rec.id == receipt.id for rec in self.receipts):
            raise ExistsError(f"Receipt with ID {receipt.id} already exists.")

        self.receipts.append(deepcopy(receipt))
        self.shifts.add_receipt_to_shift(receipt)
        return receipt

    def close_receipt(self, receipt_id: str) -> None:
        for receipt in self.receipts:
            if receipt.id == receipt_id:
                if receipt.status == "closed":
                    raise DoesntExistError(
                        f"Receipt with ID {receipt_id} is already closed."
                    )
                receipt.status = "closed"
                return
        raise DoesntExistError(f"Receipt with ID {receipt_id} does not exist.")

    def get_receipt(self, receipt_id: str) -> Receipt:
        for receipt in self.receipts:
            if receipt.id == receipt_id:
                return receipt
        raise DoesntExistError(f"Receipt with ID {receipt_id} does not exist.")

    def add_product_to_receipt(
        self, receipt_id: str, product_request: AddProductRequest
    ) -> Receipt:
        product_price = 0
        product_found = False
        for product in self.products.read_all_products():
            if product.id == product_request.product_id:
                product_price = product.price
                product_found = True
                break

        if product_found is False:
            raise (
                DoesntExistError(
                    f"Product with ID {product_request.product_id} does not exist."
                )
            )

        for receipt in self.receipts:
            if receipt.id == receipt_id:
                total_price = product_request.quantity * product_price

                product = ReceiptProduct(
                    id=product_request.product_id,
                    quantity=product_request.quantity,
                    price=product_price,
                    total=total_price,
                )

                receipt.products.append(deepcopy(product))
                receipt.total += total_price

                return receipt
        raise DoesntExistError(f"Receipt with ID {receipt_id} does not exist.")

    def calculate_payment(
        self,
        receipt_id: str,
    ) -> ReceiptForPayment:
        # receipt = self.get_receipt(receipt_id)
        pass
