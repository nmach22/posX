from copy import deepcopy
from dataclasses import field
from dataclasses import dataclass
from typing import Dict

from app.core.Interfaces.receipt_interface import Receipt
from app.core.Interfaces.shift_interface import Shift, Report, SalesReport
from app.core.Interfaces.shift_repository_interface import ShiftRepositoryInterface
from app.infra.in_memory_repositories.product_in_memory_repository import (
    DoesntExistError,
)


@dataclass
class ShiftInMemoryRepository(ShiftRepositoryInterface):
    shifts: list[Shift] = field(default_factory=list)

    def add_shift(self, shift: Shift) -> None:
        self.shifts.append(deepcopy(shift))

    def close_shift(self, shift_id: str) -> None:
        for shift in self.shifts:
            if shift.shift_id == shift_id:
                shift.status = "closed"
                return
        raise DoesntExistError(f"Shift with ID {shift_id} not found.")

    def add_receipt_to_shift(self, receipt: Receipt):
        for shift in self.shifts:
            if shift.shift_id == receipt.shift_id:
                shift.receipts.append(deepcopy(receipt))
                return
        raise DoesntExistError(f"Shift with ID {receipt.shift_id} not found.")

    def get_x_report(self, shift_id: str) -> Report:
        for shift in self.shifts:
            if shift.shift_id == shift_id:
                print("shift ipova da axla statusi unda sheamowmos")
                if shift.status != "open":
                    print("shift status = closed")
                    raise ValueError(
                        f"Cannot generate X Report for closed shift {shift_id}."
                    )

                print("shift status = open")

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
                    {
                        "id": pid,
                        "quantity": data["quantity"],
                        "total_price": data["total_price"],
                    }
                    for pid, data in product_summary.items()
                ]

                return Report(
                    shift_id=shift_id,
                    n_receipts=n_receipts,
                    revenue=revenue,
                    products=products,
                )
        raise DoesntExistError(f"Shift with ID {shift_id} not found.")

    def get_z_report(self, shift_id: str) -> Report:
        for shift in self.shifts:
            if shift.shift_id == shift_id:
                print("shift ipova da axla statusi unda sheamowmos")
                if shift.status != "open":
                    print("shift status = closed")
                    raise ValueError(
                        f"Cannot generate Z Report for closed shift {shift_id}."
                    )

                print("shift status = open")
                receipts = shift.receipts
                n_receipts = len(receipts)
                revenue = sum(r.total for r in receipts)

                product_summary = {}

                for receipt in receipts:
                    for product in receipt.products:
                        if product.id not in product_summary:
                            product_summary[product.id] = 0
                        product_summary[product.id] += product.quantity

                products = [
                    {"id": pid, "quantity": quantity}
                    for pid, quantity in product_summary.items()
                ]

                self.close_shift(shift_id)
                return Report(
                    shift_id=shift_id,
                    n_receipts=n_receipts,
                    revenue=revenue,
                    products=products,
                )
        raise DoesntExistError(f"Shift with ID {shift_id} not found.")

    def get_lifetime_sales_report(self) -> SalesReport:
        total_revenue = 0
        total_receipts = 0
        product_summary: Dict[str, Dict[str, float]] = {}

        for shift in self.shifts:
            for receipt in shift.receipts:
                if receipt.status == "closed":
                    total_receipts += 1
                    total_revenue += receipt.total

                    for product in receipt.products:
                        if product.id not in product_summary:
                            product_summary[product.id] = {
                                "quantity": 0,
                                "total_price": 0.0,
                            }

                        product_summary[product.id]["quantity"] += product.quantity
                        product_summary[product.id]["total_price"] += product.total

        products = [
            {
                "id": pid,
                "quantity": data["quantity"],
                "total_price": data["total_price"],
            }
            for pid, data in product_summary.items()
        ]

        return SalesReport(
            total_receipts=total_receipts,
            total_revenue=total_revenue,
            products=products,
        )
