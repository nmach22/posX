from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Dict

from app.core.classes.errors import DoesntExistError, OpenReceiptsError
from app.core.Interfaces.receipt_interface import Receipt
from app.core.Interfaces.shift_interface import (
    ClosedReceipt,
    Report,
    SalesReport,
    Shift,
)
from app.core.Interfaces.shift_repository_interface import ShiftRepositoryInterface


@dataclass
class ShiftInMemoryRepository(ShiftRepositoryInterface):
    shifts: list[Shift] = field(default_factory=list)

    def create(self, shift: Shift) -> Shift:
        self.shifts.append(deepcopy(shift))
        return shift

    def update(self, shift: Shift) -> None:
        find: bool = False
        for _shift in self.shifts:
            if _shift.shift_id == shift.shift_id:
                for _receipt in _shift.receipts:
                    if _receipt.status == "open":
                        raise OpenReceiptsError(
                            "Shift cannot be closed while there are open receipts."
                        )
                self.shifts.remove(_shift)
                self.shifts.append(shift)
                return
        if not find:
            raise DoesntExistError

    def add_receipt_to_shift(self, receipt: Receipt) -> None:
        new_receipt_id = receipt.id
        for shift in self.shifts:
            if shift.shift_id == receipt.shift_id:
                for _receipt in shift.receipts:
                    if _receipt.id == new_receipt_id:
                        shift.receipts.remove(_receipt)

                shift.receipts.append(deepcopy(receipt))
                return
        raise DoesntExistError(f"Shift with ID {receipt.shift_id} not found.")

    def get_x_report(self, shift_id: str) -> Report:
        shift = next((s for s in self.shifts if s.shift_id == shift_id), None)
        if not shift:
            raise DoesntExistError(f"Shift with ID {shift_id} not found.")
        if shift.status != "open":
            raise ValueError(f"Cannot generate X Report for closed shift {shift_id}.")
        n_receipts = 0
        currency_revenue: Dict[str, float] = {}
        product_summary: Dict[str, Dict[str, Any]] = {}

        for receipt in shift.receipts:
            if receipt.status == "closed":
                n_receipts += 1
                currency_revenue[receipt.currency] = (
                    currency_revenue.get(receipt.currency, 0) + receipt.discounted_total
                )

                for product in receipt.products:
                    if product.id not in product_summary:
                        product_summary[product.id] = {"quantity": 0}
                    product_summary[product.id]["quantity"] += product.quantity

        products = [
            {"id": str(pid), "quantity": int(data["quantity"])}
            for pid, data in product_summary.items()
        ]

        return Report(
            shift_id=shift_id,
            n_receipts=n_receipts,
            revenue=currency_revenue,
            products=products,
        )

    def get_lifetime_sales_report(self) -> SalesReport:
        total_receipts = 0
        currency_totals: Dict[str, float] = {}
        closed_receipts: list[ClosedReceipt] = []

        for shift in self.shifts:
            for receipt in shift.receipts:
                if receipt.status == "closed":
                    total_receipts += 1
                    currency_totals[receipt.currency] = (
                        currency_totals.get(receipt.currency, 0)
                        + receipt.discounted_total
                    )

                    closed_receipts.append(
                        ClosedReceipt(
                            receipt_id=receipt.id, calculated_payment=receipt.total
                        )
                    )

        return SalesReport(
            total_receipts=total_receipts,
            total_revenue=currency_totals,
            closed_receipts=closed_receipts,
        )

    def read_all_shifts(self) -> list[Shift]:
        return self.shifts

    def delete(self, shift_id: str) -> None:
        raise NotImplementedError("Not implemented yet.")

    def read(self, shift_id: str) -> Shift:
        for shift in self.shifts:
            if shift.shift_id == shift_id:
                return shift
        raise DoesntExistError

    def read_all(self) -> list[Shift]:
        raise NotImplementedError("Not implemented yet.")
