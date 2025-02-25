from dataclasses import dataclass, field

from app.core.Interfaces.product_interface import Product
from app.core.Interfaces.product_repository_interface import ProductRepositoryInterface
from app.infra.product_in_memory_repository import ProductInMemoryRepository


@dataclass
class InMemory:
    _products: ProductInMemoryRepository = field(
        init=False,
        default_factory=ProductInMemoryRepository,
    )

    def products(self) -> ProductRepositoryInterface:
        return self._products
