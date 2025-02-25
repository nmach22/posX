from dataclasses import dataclass

from app.core.Interfaces.product_interface import Product
from app.core.Interfaces.product_repository_interface import ProductRepositoryInterface


class ExistsError(Exception):
    pass


class DoesntExistError(Exception):
    pass


@dataclass
class ProductInMemoryRepository(ProductRepositoryInterface):
    products: list[Product]

    def add_product(self, product: Product) -> None:
        for exicting_product in self.products:
            if exicting_product.barcode == product.barcode:
                raise ExistsError(product.barcode)

        self.products.append(product)

    def get_product(self, product_id: str) -> Product:
        for product in self.products:
            if product.id == product_id:
                return product

        raise DoesntExistError

    def update_product(self, new_price: int, product_id: str) -> None:
        find: bool = False
        for product in self.products:
            if product.id == product_id:
                find = True
                product.price = new_price

        if not find:
            raise DoesntExistError

    def read_all_products(self) -> list[Product]:
        return self.products
