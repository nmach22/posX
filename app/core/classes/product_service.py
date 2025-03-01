import uuid
from dataclasses import dataclass

from app.core.Interfaces.product_interface import (
    Product,
    ProductInterface,
    ProductRequest,
)
from app.core.Interfaces.product_repository_interface import ProductRepositoryInterface
from app.infra.in_memory_repositories.product_in_memory_repository import (
    DoesntExistError,
    ExistsError,
)


@dataclass
class ProductService(ProductInterface):
    repository: ProductRepositoryInterface

    def create_product(self, product_request: ProductRequest) -> Product:
        name = product_request.name
        price = product_request.price
        barcode = product_request.barcode
        product_id = uuid.uuid4()
        product = Product(id=str(product_id), name=name, price=price, barcode=barcode)
        try:
            self.repository.add_product(product)
            return product
        except ExistsError:
            raise ExistsError

    def read_all_products(self) -> list[Product]:
        return self.repository.read_all_products()

    def update_product_price(self, product: Product) -> None:
        try:
            self.repository.update_product(product)
        except DoesntExistError:
            raise DoesntExistError

    def get_product(self, product_id: str) -> Product:
        try:
            product = self.repository.get_product(product_id)
            return product
        except DoesntExistError:
            raise DoesntExistError
