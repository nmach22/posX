import uuid
from dataclasses import dataclass

from app.core.Interfaces.receipt_interface import Receipt
from app.core.Interfaces.shift_interface import (
    Report,
    SalesReport,
    Shift,
    ShiftInterface,
)
from app.core.Interfaces.shift_repository_interface import ShiftRepositoryInterface
from app.infra.in_memory_repositories.product_in_memory_repository import (
    DoesntExistError,
)


@dataclass
class ShiftService(ShiftInterface):
    repository: ShiftRepositoryInterface

    def create_shift(self) -> Shift:
        shift_id = uuid.uuid4()
        shift = Shift(shift_id=str(shift_id), receipts=[], status="open")
        self.repository.create(shift)
        return shift

    def close_shift(self, shift_id: str) -> None:
        try:
            existing_shift = self.get_shift(shift_id)
        except DoesntExistError:
            raise DoesntExistError
        if existing_shift.status != "open":
            raise ValueError("shift is closed already")
        updated_shift = Shift(
            shift_id=existing_shift.shift_id,
            receipts=existing_shift.receipts,
            status="closed",
        )
        try:
            self.repository.update(updated_shift)
        except DoesntExistError:
            raise DoesntExistError

    def add_receipt_to_shift(self, receipt: Receipt) -> None:
        self.repository.add_receipt_to_shift(receipt)

    def get_x_report(self, shift_id: str) -> Report:
        return self.repository.get_x_report(shift_id)

    def get_lifetime_sales_report(self) -> SalesReport:
        return self.repository.get_lifetime_sales_report()

    def get_shift(self, shift_id: str) -> Shift:
        try:
            shift = self.repository.read(shift_id)
            return shift
        except DoesntExistError:
            raise DoesntExistError
