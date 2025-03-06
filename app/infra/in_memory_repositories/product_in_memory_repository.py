from dataclasses import dataclass, field

from app.core.Interfaces.product_interface import Product
from app.core.Interfaces.repository import Repository
from app.core.classes.errors import ExistsError, DoesntExistError


@dataclass
class ProductInMemoryRepository(Repository[Product]):
    products: list[Product] = field(default_factory=list)

    def create(self, product: Product) -> Product:
        for existing_product in self.products:
            if existing_product.barcode == product.barcode:
                raise ExistsError(product.barcode)

        self.products.append(product)
        return product

    def read(self, product_id: str) -> Product:
        for product in self.products:
            if product.id == product_id:
                return product
        raise DoesntExistError

    def update(self, product: Product) -> None:
        find: bool = False
        for _product in self.products:
            if _product.id == product.id:
                self.products.remove(_product)
                self.products.append(product)
                return
        if not find:
            raise DoesntExistError

    def read_all(self) -> list[Product]:
        return self.products

    def delete(self, product_id: str) -> None:
        raise NotImplementedError("Not implemented yet.")