import uuid
from dataclasses import dataclass

from app.core.Interfaces.receipt_interface import Receipt
from app.core.Interfaces.shift_interface import Shift, ShiftInterface, XReport, ZReport, SalesReport
from app.core.Interfaces.shift_repository_interface import ShiftRepositoryInterface


@dataclass
class ShiftService(ShiftInterface):
    repository: ShiftRepositoryInterface

    def create_shift(self) -> Shift:
        shift_id = uuid.uuid4()
        shift = Shift(shift_id=str(shift_id), receipts=[], status="open")
        self.repository.add_shift(shift)
        return shift

    def close_shift(self, shift_id: str) -> None:
        self.repository.close_shift(shift_id)

    def add_receipt_to_shift(self, receipt: Receipt) -> None:
        self.repository.add_receipt_to_shift(receipt)

    def get_x_report(self, shift_id: str) -> XReport:
        return self.repository.get_x_report(shift_id)

    def get_z_report(self, shift_id: str) -> ZReport:
        return self.repository.get_z_report(shift_id)

    def get_lifetime_sales_report(self) -> SalesReport:
        return self.repository.get_lifetime_sales_report()

