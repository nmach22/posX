from dataclasses import dataclass
from typing import Dict, Protocol

from app.core.Interfaces.receipt_interface import Receipt


@dataclass
class Shift:
    shift_id: str
    receipts: list[Receipt]
    status: str


@dataclass
class Report:
    shift_id: str
    n_receipts: int
    revenue: int
    products: list[Dict[str, int]]


@dataclass
class SalesReport:
    total_receipts: int
    total_revenue: float
    products: list[dict[str, float | int]]


class ShiftInterface(Protocol):
    def create_shift(self) -> Shift:
        pass

    def close_shift(self, shift_id: str) -> None:
        pass

    def add_receipt_to_shift(self, receipt: Receipt) -> None:
        pass

    def get_x_report(self, shift_id: str) -> Report:
        pass

    def get_z_report(self, shift_id: str) -> Report:
        pass

    def get_lifetime_sales_report(self) -> SalesReport:
        pass
