from typing import Protocol

from app.core.Interfaces.receipt_interface import Receipt
from app.core.Interfaces.shift_interface import Report, SalesReport, Shift


class ShiftRepositoryInterface(Protocol):
    def create(self, item: Shift) -> Shift:
        pass

    def update(self, item_id: str) -> None:
        pass

    def add_receipt_to_shift(self, receipt: Receipt):
        pass

    def get_x_report(self, shift_id: str) -> Report:
        pass

    def get_lifetime_sales_report(self) -> SalesReport:
        pass
