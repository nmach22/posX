import uuid

from app.core.classes.shift_service import ShiftService
from app.core.Interfaces.product_interface import Product
from app.core.Interfaces.receipt_interface import Receipt, ReceiptProduct
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
    receipt = Receipt(
        id=str(uuid.uuid4()),
        shift_id=shift.shift_id,
        products=[product],
        status="open",
        total=100,
    )

    service.add_receipt_to_shift(receipt)

    assert len(shift_list[0].receipts) == 1
    assert shift_list[0].receipts[0].id == receipt.id
    assert shift_list[0].receipts[0].total == 100


def test_should_generate_x_report() -> None:
    shift_list: list[Shift] = []
    service = ShiftService(ShiftInMemoryRepository(shift_list))
    shift = service.create_shift()
    product1 = ReceiptProduct(id="p1", quantity=2, price=50, total=100)
    product2 = ReceiptProduct(id="p2", quantity=1, price=150, total=150)
    receipt1 = Receipt(
        id="r1",
        shift_id=shift.shift_id,
        products=[product1, product2],
        status="closed",
        total=250,
    )
    receipt2 = Receipt(
        id="r2",
        shift_id=shift.shift_id,
        products=[product1],
        status="closed",
        total=100,
    )
    service.add_receipt_to_shift(receipt1)
    service.add_receipt_to_shift(receipt2)

    x_report = service.get_x_report(shift.shift_id)

    assert x_report.shift_id == shift.shift_id
    assert x_report.n_receipts == 2
    assert x_report.revenue == 350
    assert len(x_report.products) == 2
    assert x_report.products[0]["quantity"] == 4
    assert x_report.products[0]["total_price"] == 200
    assert x_report.products[1]["quantity"] == 1
    assert x_report.products[1]["total_price"] == 150


def test_get_z_report():
    shift_list: list[Shift] = []
    service = ShiftService(ShiftInMemoryRepository(shift_list))

    shift = service.create_shift()
    receipt = Receipt(
        id=str(uuid.uuid4()),
        shift_id=shift.shift_id,
        products=[],
        status="open",
        total=100,
    )
    service.add_receipt_to_shift(receipt)
    z_report = service.get_z_report(shift.shift_id)

    # Assertions
    assert z_report.shift_id == shift.shift_id
    assert z_report.n_receipts == 1
    assert z_report.revenue == 100.0
    assert shift_list[0].status == "closed"
