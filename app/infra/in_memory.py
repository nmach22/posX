from dataclasses import dataclass, field
from itertools import product

from app.core.Interfaces.campaign_repository_interface import (
    CampaignRepositoryInterface,
)
from app.core.Interfaces.product_repository_interface import ProductRepositoryInterface
from app.core.Interfaces.receipt_repository_interface import ReceiptRepositoryInterface
from app.infra.campaign_in_memory_repository import CampaignInMemoryRepository
from app.core.Interfaces.shift_repository_interface import ShiftRepositoryInterface
from app.infra.campaign_in_memory_repository import CampaignInMemoryRepository
from app.infra.product_in_memory_repository import ProductInMemoryRepository
from app.infra.receipt_in_memory_repository import ReceiptInMemoryRepository
from app.infra.shift_in_memory_repository import ShiftInMemoryRepository


@dataclass
class InMemory:
    _products: ProductInMemoryRepository = field(
        init=False,
        default_factory=ProductInMemoryRepository,
    )

    _shifts: ShiftInMemoryRepository = field(
        init=False, default_factory=ShiftInMemoryRepository
    )

    _receipts: ReceiptInMemoryRepository = field(
        init=False,
    )

    _campaigns: CampaignInMemoryRepository = field(
        init=False,
    )

    def __post_init__(self):
        # self._shifts = ShiftInMemoryRepository(shifts=[])

        self._campaigns = CampaignInMemoryRepository(
            products_repo=self._products,
        )
        self._receipts = ReceiptInMemoryRepository(
            products=self._products, shifts=self._shifts, campaigns=self._campaigns
        )

    def products(self) -> ProductRepositoryInterface:
        return self._products

    def receipts(self) -> ReceiptRepositoryInterface:
        return self._receipts

    def campaigns(self) -> CampaignRepositoryInterface:
        return self._campaigns

    def shifts(self) -> ShiftRepositoryInterface:
        return self._shifts
