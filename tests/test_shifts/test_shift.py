import uuid

from app.core.classes.shift_service import ShiftService
from app.core.Interfaces.product_interface import Product
from app.core.Interfaces.receipt_interface import Receipt
from app.core.Interfaces.shift_interface import Shift
from app.infra.shift_in_memory_repository import ShiftInMemoryRepository


def test_should_create_shift() -> None:
    shift_list: list[Shift] = []
    service = ShiftService(ShiftInMemoryRepository(shift_list))
    shift = service.create_shift()

    assert len(shift_list) == 1
    assert shift_list[0].shift_id == shift.shift_id
    assert shift_list[0].status == "open"
    assert shift_list[0].receipts == []


def test_should_close_shift() -> None:
    shift_list: list[Shift] = []
    service = ShiftService(ShiftInMemoryRepository(shift_list))
    shift = service.create_shift()
    service.close_shift(shift.shift_id)

    assert shift_list[0].status == "closed"


def test_should_add_receipt_to_shift() -> None:
    shift_list: list[Shift] = []
    service = ShiftService(ShiftInMemoryRepository(shift_list))
    shift = service.create_shift()
    product = Product(id=str(uuid.uuid4()), name="Product1", price=100, barcode="123")
    receipt = Receipt(id=str(uuid.uuid4()), products=[product], status="open", total=100)

    service.add_receipt_to_shift(receipt, shift.shift_id)

    assert len(shift_list[0].receipts) == 1
    assert shift_list[0].receipts[0].id == receipt.id
    assert shift_list[0].receipts[0].total == 100

#
# def test_should_get_x_report() -> None:
#     shift_list: list[Shift] = []
#     service = ShiftService(ShiftInMemoryRepository(shift_list))
#     shift = service.create_shift()
#     product1 = Product(id=str(uuid.uuid4()), name="Product1", price=200, barcode="111")
#     product2 = Product(id=str(uuid.uuid4()), name="Product2", price=300, barcode="222")
#     receipt1 = Receipt(id=str(uuid.uuid4()), products=[product1], status="closed", total=200)
#     receipt2 = Receipt(id=str(uuid.uuid4()), products=[product2], status="closed", total=300)
#
#     service.add_receipt_to_shift(receipt1, shift.shift_id)
#     service.add_receipt_to_shift(receipt2, shift.shift_id)
#
#     report = service.get_x_report(shift.shift_id)
#
#     assert report.shift_id == shift.shift_id
#     assert report.n_receipts == 2
