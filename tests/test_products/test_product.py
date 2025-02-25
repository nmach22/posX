import pytest

from app.core.classes.product_service import ProductService
from app.core.Interfaces.product_interface import Product, ProductRequest
from app.infra.product_in_memory_repository import (
    DoesntExistError,
    ExistsError,
    ProductInMemoryRepository,
)


def test_should_add_product_in_memory() -> None:
    product_list: list[Product] = []
    service = ProductService(ProductInMemoryRepository(product_list))
    service.create_product(ProductRequest("lobio", 500, "123123"))
    assert len(product_list) == 1
    assert product_list[0].name == "lobio"


def test_add_and_read_product() -> None:
    product_list: list[Product] = []
    service = ProductService(ProductInMemoryRepository(product_list))
    product = service.create_product(ProductRequest("lobio", 500, "123123"))
    returned_product = service.get_product(product.id)
    assert returned_product.name == "lobio"
    assert returned_product.price == 500
    assert returned_product.barcode == "123123"


def test_update_product() -> None:
    product_list: list[Product] = []
    service = ProductService(ProductInMemoryRepository(product_list))
    product = service.create_product(ProductRequest("lobio", 500, "123123"))

    service.update_product_price(
        Product(product.id, product.name, 1000, product.barcode)
    )
    new_product = service.get_product(product.id)
    assert new_product.price == 1000


def test_read_all_products() -> None:
    product_list: list[Product] = []
    service = ProductService(ProductInMemoryRepository(product_list))
    product1 = service.create_product(ProductRequest("lobio", 500, "123123"))
    product2 = service.create_product(ProductRequest("mchadi", 3, "1234"))
    all_product = service.read_all_products()
    assert len(all_product) == 2


def test_adding_existing_product() -> None:
    product_list: list[Product] = []
    service = ProductService(ProductInMemoryRepository(product_list))
    service.create_product(ProductRequest("lobio", 500, "123123"))
    with pytest.raises(ExistsError):
        service.create_product(ProductRequest("lobio", 500, "123123"))


def test_getting_non_existing_product() -> None:
    product_list: list[Product] = []
    service = ProductService(ProductInMemoryRepository(product_list))
    with pytest.raises(DoesntExistError):
        service.get_product("123")


def test_updaiting_non_existing_product() -> None:
    product_list: list[Product] = []
    service = ProductService(ProductInMemoryRepository(product_list))
    with pytest.raises(DoesntExistError):
        service.update_product_price(1000, "123")
