from copy import deepcopy
from dataclasses import dataclass

from app.core.Interfaces.product_interface import Product


@dataclass
class ProductInMemoryRepository:
    products: list[Product]

    def add_product(self, product: Product) -> None:
        self.products.append(deepcopy(product))
