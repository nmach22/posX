from copy import deepcopy
from dataclasses import dataclass

from app.core.Interfaces.product_interface import Product


@dataclass
class ProductInMemoryRepository:
    products: list[Product]

    def add_product(self, product: Product) -> None:
        self.products.append(deepcopy(product))

    def get_product(self, product_id: int) -> Product:
        for product in self.products:
            if product.id == product_id:
                return deepcopy(product)
