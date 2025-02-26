from dataclasses import dataclass, field

from app.core.Interfaces.product_repository_interface import ProductRepositoryInterface
from app.core.Interfaces.receipt_repository_interface import ReceiptRepositoryInterface
from app.infra.product_in_memory_repository import ProductInMemoryRepository
from app.infra.receipt_in_memory_repository import ReceiptInMemoryRepository


@dataclass
class InMemory:
    _products: ProductInMemoryRepository = field(
        init=False,
        default_factory=ProductInMemoryRepository,
    )

    _receipts: ReceiptInMemoryRepository = field(
        init=False,
    )

    def __post_init__(self):
        self._receipts = ReceiptInMemoryRepository(products=self._products)

    def products(self) -> ProductRepositoryInterface:
        return self._products

    def receipts(self) -> ReceiptRepositoryInterface:
        return self._receipts
