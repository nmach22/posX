from dataclasses import dataclass, field

from app.core.Interfaces.product_interface import Product
from app.core.Interfaces.product_repository_interface import ProductRepositoryInterface


@dataclass
class ProductInMemoryRepository(ProductRepositoryInterface):
    products: list[Product] = field(default_factory=list)

    def add_product(self, product: Product) -> None:
        self.products.append(product)

    def get_product(self, product_id: str) -> Product:
        for product in self.products:
            if product.id == product_id:
                return product

    def update_product(self, product: Product) -> None:
        for _product in self.products:
            if _product.id == product.id:
                self.products.remove(_product)
                self.products.append(product)
                return

    def read_all_products(self) -> list[Product]:
        return self.products
