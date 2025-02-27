from typing import Protocol

from app.core.Interfaces.receipt_interface import Receipt
from app.core.Interfaces.shift_interface import Shift, Report, Report, SalesReport


class ShiftRepositoryInterface(Protocol):
    def add_shift(self, shift: Shift) -> None:
        pass

    def close_shift(self, shift_id: str) -> None:
        pass

    def add_receipt_to_shift(self, receipt: Receipt):
        pass

    def get_x_report(self, shift_id: str) -> Report:
        pass

    def get_z_report(self, shift_id: str) -> Report:
        pass

    def get_lifetime_sales_report(self) -> SalesReport:
        pass
