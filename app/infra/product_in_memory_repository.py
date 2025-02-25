from dataclasses import dataclass

from app.core.Interfaces.product_interface import Product
from app.core.Interfaces.product_repository_interface import ProductRepositoryInterface


@dataclass
class ProductInMemoryRepository(ProductRepositoryInterface):
    products: list[Product]

    def add_product(self, product: Product) -> None:
        self.products.append(product)

    def get_product(self, product_id: str) -> Product:
        for product in self.products:
            if product.id == product_id:
                return product

    def update_product(self, new_price: int, product_id: str) -> None:
        for product in self.products:
            if product.id == product_id:
                product.price = new_price


    def read_all_products(self) -> list[Product]:
        return self.products