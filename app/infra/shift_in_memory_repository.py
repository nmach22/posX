from copy import deepcopy
from dataclasses import dataclass

from app.core.Interfaces.receipt_interface import Receipt
from app.core.Interfaces.shift_interface import Shift
from app.core.Interfaces.shift_repository_interface import ShiftRepositoryInterface


@dataclass
class ShiftInMemoryRepository(ShiftRepositoryInterface):
    shifts: list[Shift]
    receipts: list[Receipt]

    def add_shift(self, shift: Shift) -> None:
        self.shifts.append(deepcopy(shift))

    def close_shift(self, shift_id: str) -> None:
        for shift in self.shifts:
            if shift.shift_id == shift_id:
                shift.status = "closed"

    def add_receipt_to_shift(self, receipt: Receipt, shift_id: str):
        for shift in self.shifts:
            if shift.shift_id == shift_id:
                shift.receipts.append(deepcopy(receipt))

    # class XReport:
    #     shift_id: str
    #     n_receipts: int
    #     revenue: int
    #     products: list[Dict[str, int]]
    #
    # @dataclass
    # class Receipt:
    #     id: str
    #     products: list[Product]
    #     status: str
    #     total: int

    # def get_x_report(self, shift_id: str) -> XReport:
    #     for shift in self.shifts:
    #         if shift.shift_id == shift_id:
    #             total_revenue = sum(receipt.total for receipt in shift.receipts if receipt.status == "closed")
    #             product_counts = {}
    #
    #             for receipt in shift.receipts:
    #                 if receipt.status == "closed":
    #                     for product in receipt.products:
    #                         product_counts[product.name] = product_counts.get(product.name, 0) + product.quantity
    #
    #             return XReport(
    #                 shift_id=shift_id,
    #                 n_receipts=len(shift.receipts),
    #                 revenue=total_revenue,
    #                 products=[{"name": name, "quantity": quantity} for name, quantity in product_counts.items()]
    #             )
    #
    #     raise ValueError(f"Shift with ID {shift_id} not found")
    #
    #
