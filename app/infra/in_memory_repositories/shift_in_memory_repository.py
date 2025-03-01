from copy import deepcopy
from dataclasses import dataclass, field
from typing import Dict

from app.core.Interfaces.receipt_interface import Receipt
from app.core.Interfaces.shift_interface import (
    ClosedReceipt,
    Report,
    SalesReport,
    Shift,
)
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
                if shift.status != "open":
                    raise ValueError(f"Shift with ID {shift_id} is already closed.")
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
        shift = next((s for s in self.shifts if s.shift_id == shift_id), None)
        if not shift:
            raise DoesntExistError(f"Shift with ID {shift_id} not found.")
        if shift.status != "open":
            raise ValueError(f"Cannot generate X Report for closed shift {shift_id}.")
        n_receipts = 0
        currency_revenue: Dict[str, int] = {}
        product_summary: Dict[str, Dict[str, int]] = {}

        for receipt in shift.receipts:
            if receipt.status == "closed":
                n_receipts += 1
                currency_revenue[receipt.currency] = (
                    currency_revenue.get(receipt.currency, 0) + receipt.total
                )

                for product in receipt.products:
                    if product.id not in product_summary:
                        product_summary[product.id] = {"quantity": 0}
                    product_summary[product.id]["quantity"] += product.quantity

        products = [
            {"id": pid, "quantity": data["quantity"]}
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
        currency_totals: Dict[str, int] = {}  # Supports multiple currencies
        closed_receipts: list[ClosedReceipt] = []

        for shift in self.shifts:
            for receipt in shift.receipts:
                if receipt.status == "closed":
                    total_receipts += 1
                    currency_totals[receipt.currency] = (
                        currency_totals.get(receipt.currency, 0) + receipt.total
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
