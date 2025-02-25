from copy import deepcopy
from dataclasses import dataclass

from app.core.Interfaces.receipt_interface import Receipt
from app.core.Interfaces.shift_interface import Shift, XReport
from app.core.Interfaces.shift_repository_interface import ShiftRepositoryInterface
from app.infra.product_in_memory_repository import DoesntExistError


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
                return
        raise DoesntExistError(f"Shift with ID {shift_id} not found.")

    def add_receipt_to_shift(self, receipt: Receipt, shift_id: str):
        for shift in self.shifts:
            if shift.shift_id == shift_id:
                shift.receipts.append(deepcopy(receipt))
                return
        raise DoesntExistError(f"Shift with ID {shift_id} not found.")


    def get_x_report(self, shift_id: str) -> XReport:
        for shift in self.shifts:
            if shift.shift_id == shift_id:
                receipts = [r for r in shift.receipts if r.status == "closed"]
                n_receipts = len(receipts)
                revenue = sum(r.total for r in receipts)

                product_summary = {}
                for receipt in receipts:
                    for product in receipt.products:
                        if product.id not in product_summary:
                            product_summary[product.id] = {
                                "quantity": 0,
                                "total_price": 0.0,
                            }
                        product_summary[product.id]["quantity"] += product.quantity
                        product_summary[product.id]["total_price"] += product.total

                products = [
                    {"id": pid, "quantity": data["quantity"],
                     "total_price": data["total_price"]}
                    for pid, data in product_summary.items()
                ]

                return XReport(shift_id=shift_id, n_receipts=n_receipts,
                               revenue=revenue, products=products)
            raise DoesntExistError(f"Shift with ID {shift_id} not found.")