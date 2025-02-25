import uuid
from dataclasses import dataclass

from app.core.Interfaces.product_interface import Product, ProductRequest
from app.core.Interfaces.product_repository_interface import ProductRepositoryInterface


@dataclass
class ProductService:
    repository: ProductRepositoryInterface

    def create_product(self, product_request: ProductRequest) -> Product:
        name = product_request.name
        price = product_request.price
        barcode = product_request.barcode
        product_id = uuid.uuid4()
        product = Product(name=name, price=price, barcode=barcode, id=str(product_id))
        self.repository.add_product(product)
        return product


    def read_all_products(self, product_id: str) -> list[Product]:
        pass

    def update_product_price(self, new_price: int, product_id: str) -> None:
        pass

    def get_product(self, product_id: str) -> Product:
        return self.repository.get_product(product_id)
