import pytest

from app.core.Interfaces.product_interface import Product
from app.core.classes.receipt_service import ReceiptService
from app.core.Interfaces.product_interface import Product
from app.core.Interfaces.receipt_interface import AddProductRequest, Receipt
from app.infra.product_in_memory_repository import (
    DoesntExistError,
    ProductInMemoryRepository,
)
from app.infra.receipt_in_memory_repository import ReceiptInMemoryRepository


def test_should_add_receipt_in_memory() -> None:
    receipt_list: list[Receipt] = []
    service = ReceiptService(ReceiptInMemoryRepository(receipt_list))
    service.create_receipt()
    assert len(receipt_list) == 1
    assert receipt_list[0].status == "open"
    assert len(receipt_list[0].products) == 0
    assert receipt_list[0].total == 0


def test_should_close_receipt_in_memory() -> None:
    receipt_list: list[Receipt] = []
    service = ReceiptService(ReceiptInMemoryRepository(receipt_list))

    receipt = service.create_receipt()
    receipt_id = receipt.id

    assert receipt.status == "open"
    service.close_receipt(receipt_id)
    assert receipt_list[0].status == "closed"


def test_should_read_receipt_in_memory() -> None:
    receipt_list: list[Receipt] = []
    service = ReceiptService(ReceiptInMemoryRepository(receipt_list))

    receipt = service.create_receipt()
    receipt_id = receipt.id

    retrieved_receipt = service.read_receipt(receipt_id)

    assert retrieved_receipt is not None
    assert retrieved_receipt.id == receipt_id
    assert retrieved_receipt.status == "open"
    assert retrieved_receipt.products == []
    assert retrieved_receipt.total == 0


def test_should_add_product_to_receipt() -> None:
    receipt_list: list[Receipt] = []
    product_list: list[Product] = [Product("123", "sigareti", 10, "12345")]
    service = ReceiptService(
        ReceiptInMemoryRepository(receipt_list, ProductInMemoryRepository(product_list))
    )

    receipt = service.create_receipt()
    receipt_id = receipt.id

    product_request = AddProductRequest(product_id="123", quantity=2)
    updated_receipt = service.add_product(receipt_id, product_request)

    assert len(updated_receipt.products) == 1
    assert updated_receipt.products[0].id == "123"
    assert updated_receipt.products[0].quantity == 2
    assert updated_receipt.products[0].price == 10.0
    assert updated_receipt.products[0].total == 20.0
    assert updated_receipt.total == 20.0


def test_should_raise_error_when_reading_nonexistent_receipt() -> None:
    receipt_list: list[Receipt] = []
    service = ReceiptService(
        ReceiptInMemoryRepository(receipt_list, ProductInMemoryRepository())
    )

    with pytest.raises(
        DoesntExistError, match="Receipt with ID nonexistent_id does not exist."
    ):
        service.read_receipt("nonexistent_id")


def test_should_raise_error_when_closing_nonexistent_receipt() -> None:
    receipt_list: list[Receipt] = []
    service = ReceiptService(ReceiptInMemoryRepository(receipt_list))

    with pytest.raises(
        DoesntExistError, match="Receipt with ID nonexistent_id does not exist."
    ):
        service.close_receipt("nonexistent_id")


def test_should_raise_error_when_adding_product_to_nonexistent_receipt() -> None:
    receipt_list: list[Receipt] = []
    product_list: list[Product] = [Product("123", "sigareti", 10, "12345")]
    service = ReceiptService(
        ReceiptInMemoryRepository(receipt_list, ProductInMemoryRepository(product_list))
    )

    product_request = AddProductRequest(product_id="123", quantity=2)

    with pytest.raises(
        DoesntExistError, match="Receipt with ID nonexistent_id does not exist."
    ):
        service.add_product("nonexistent_id", product_request)


def test_should_raise_error_when_adding_nonexistent_product_to_receipt() -> None:
    receipt_list: list[Receipt] = []
    service = ReceiptService(ReceiptInMemoryRepository(receipt_list))

    receipt = service.create_receipt()
    receipt_id = receipt.id

    product_request = AddProductRequest(product_id="999", quantity=1)

    with pytest.raises(DoesntExistError, match="Product with ID 999 does not exist."):
        service.add_product(receipt_id, product_request)


def test_should_raise_error_when_closing_already_closed_receipt() -> None:
    receipt_list: list[Receipt] = []
    service = ReceiptService(ReceiptInMemoryRepository(receipt_list))

    receipt = service.create_receipt()
    receipt_id = receipt.id
    service.close_receipt(receipt_id)

    with pytest.raises(
        DoesntExistError, match=f"Receipt with ID {receipt_id} is already closed."
    ):
        service.close_receipt(receipt_id)
