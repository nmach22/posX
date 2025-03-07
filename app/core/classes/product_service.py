import uuid
from dataclasses import dataclass

from app.core.Interfaces.product_interface import (
    Product,
    ProductInterface,
    ProductRequest,
)
from app.core.Interfaces.repository import Repository
from app.core.classes.errors import ExistsError, DoesntExistError


@dataclass
class ProductService(ProductInterface):
    repository: Repository[Product]

    def create_product(self, product_request: ProductRequest) -> Product:
        name = product_request.name
        price = product_request.price
        barcode = product_request.barcode
        product_id = uuid.uuid4()
        product = Product(
            id=str(product_id), name=name, price=int(price * 100), barcode=barcode
        )
        try:
            self.repository.create(product)
            return product
        except ExistsError:
            raise ExistsError

    def read_all_products(self) -> list[Product]:
        return self.repository.read_all()

    def update_product_price(self, product: Product) -> None:
        try:
            self.repository.update(product)
        except DoesntExistError:
            raise DoesntExistError

    def get_product(self, product_id: str) -> Product:
        try:
            product = self.repository.read(product_id)
            return product
        except DoesntExistError:
            raise DoesntExistError
