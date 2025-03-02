import uuid

from app.core.classes.shift_service import ShiftService
from app.core.Interfaces.receipt_interface import Receipt, ReceiptProduct
from app.core.Interfaces.shift_interface import Shift
from app.infra.in_memory_repositories.shift_in_memory_repository import (
    ShiftInMemoryRepository,
)


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
    product = ReceiptProduct(id=str(uuid.uuid4()), quantity=1, price=100, total=100)
    receipt = Receipt(
        id=str(uuid.uuid4()),
        shift_id=shift.shift_id,
        currency="gel",
        products=[product],
        status="open",
        total=100,
    )

    service.add_receipt_to_shift(receipt)

    assert len(shift_list[0].receipts) == 1
    assert shift_list[0].receipts[0].id == receipt.id
    assert shift_list[0].receipts[0].total == 100


def test_close_shift():
    shift_list: list[Shift] = []
    service = ShiftService(ShiftInMemoryRepository(shift_list))

    shift = service.create_shift()
    receipt = Receipt(
        id=str(uuid.uuid4()),
        shift_id=shift.shift_id,
        currency="gel",
        products=[],
        status="open",
        total=100,
    )
    service.add_receipt_to_shift(receipt)
    service.close_shift(shift.shift_id)

    assert shift_list[0].status == "closed"


def test_should_generate_x_report_for_open_shift() -> None:
    shift_list: list[Shift] = []
    service = ShiftService(ShiftInMemoryRepository(shift_list))

    shift = service.create_shift()
    product = ReceiptProduct(id=str(uuid.uuid4()), quantity=2, price=50, total=100)
    receipt = Receipt(
        id=str(uuid.uuid4()),
        shift_id=shift.shift_id,
        currency="gel",
        products=[product],
        status="closed",  # Assuming receipts are closed for X report generation
        total=100,
    )
    service.add_receipt_to_shift(receipt)

    report = service.get_x_report(shift.shift_id)

    assert report.shift_id == shift.shift_id
    assert report.n_receipts == 1
    assert report.revenue["gel"] == 100
    assert len(report.products) == 1
    assert report.products[0]["quantity"] == 2


def test_should_raise_error_for_x_report_on_closed_shift() -> None:
    shift_list: list[Shift] = []
    service = ShiftService(ShiftInMemoryRepository(shift_list))

    shift = service.create_shift()
    service.close_shift(shift.shift_id)

    try:
        service.get_x_report(shift.shift_id)
        assert False, "Expected ValueError not raised"
    except ValueError as e:
        assert str(e) == f"Cannot generate X Report for closed shift {shift.shift_id}."


def test_should_generate_lifetime_sales_report() -> None:
    shift_list: list[Shift] = []
    service = ShiftService(ShiftInMemoryRepository(shift_list))

    shift1 = service.create_shift()
    product1 = ReceiptProduct(id=str(uuid.uuid4()), quantity=1, price=50, total=50)
    receipt1 = Receipt(
        id=str(uuid.uuid4()),
        shift_id=shift1.shift_id,
        currency="gel",
        products=[product1],
        status="closed",
        total=50,
    )
    service.add_receipt_to_shift(receipt1)

    shift2 = service.create_shift()
    product2 = ReceiptProduct(id=str(uuid.uuid4()), quantity=3, price=30, total=90)
    receipt2 = Receipt(
        id=str(uuid.uuid4()),
        shift_id=shift2.shift_id,
        currency="usd",
        products=[product2],
        status="closed",
        total=90,
    )
    service.add_receipt_to_shift(receipt2)

    report = service.get_lifetime_sales_report()

    assert report.total_receipts == 2
    assert report.total_revenue["gel"] == 50
    assert report.total_revenue["usd"] == 90
    assert len(report.closed_receipts) == 2
    assert report.closed_receipts[0].calculated_payment == 50
    assert report.closed_receipts[1].calculated_payment == 90


def test_should_generate_empty_lifetime_sales_report_for_no_closed_receipts() -> None:
    shift_list: list[Shift] = []
    service = ShiftService(ShiftInMemoryRepository(shift_list))

    shift = service.create_shift()
    product = ReceiptProduct(id=str(uuid.uuid4()), quantity=2, price=30, total=60)
    receipt = Receipt(
        id=str(uuid.uuid4()),
        shift_id=shift.shift_id,
        currency="gel",
        products=[product],
        status="open",  # Receipt is open
        total=60,
    )
    service.add_receipt_to_shift(receipt)

    report = service.get_lifetime_sales_report()

    assert report.total_receipts == 0
    assert len(report.total_revenue) == 0
    assert len(report.closed_receipts) == 0
