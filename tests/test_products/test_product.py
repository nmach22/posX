from app.core.classes.product_service import ProductService
from app.core.Interfaces.product_interface import Product, ProductRequest
from app.infra.product_in_memory_repository import ProductInMemoryRepository


def test_should_add_product_in_list() -> None:
    product_list : list[Product] = []
    service = ProductService(ProductInMemoryRepository(product_list))
    service.create_product(ProductRequest("lobio", 500, "123123"))
    assert len(product_list) == 1
    assert product_list[0].name == "lobio"
