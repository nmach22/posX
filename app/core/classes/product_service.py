import uuid
from dataclasses import dataclass

from app.core.Interfaces.product_interface import Product, ProductRequest, ProductInterface
from app.core.Interfaces.product_repository_interface import ProductRepositoryInterface


@dataclass
class ProductService(ProductInterface):
    repository: ProductRepositoryInterface

    def create_product(self, product_request: ProductRequest) -> Product:
        name = product_request.name
        price = product_request.price
        barcode = product_request.barcode
        product_id = uuid.uuid4()
        product = Product(name=name, price=price, barcode=barcode, id=str(product_id))
        self.repository.add_product(product)
        return product


    def read_all_products(self) -> list[Product]:
        return self.repository.read_all_products()

    def update_product_price(self, new_price: int, product_id: str) -> None:
        self.repository.update_product(new_price, product_id)

    def get_product(self, product_id: str) -> Product:
        return self.repository.get_product(product_id)
