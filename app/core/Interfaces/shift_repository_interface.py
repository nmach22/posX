from typing import Protocol

from app.core.Interfaces.receipt_interface import Receipt
from app.core.Interfaces.shift_interface import Shift, XReport


class ShiftRepositoryInterface(Protocol):
    def add_shift(self, shift: Shift) -> None:
        pass

    def close_shift(self, shift_id: str) -> None:
        pass

    def add_receipt_to_shift(self, receipt: Receipt, shift_id: str):
        pass

    def get_x_report(self, shift_id: str) -> XReport:
        pass
