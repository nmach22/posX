from dataclasses import dataclass, field

from app.core.classes.exchange_rate_service import ExchangeRateService
from app.core.Interfaces.campaign_interface import Campaign
from app.core.Interfaces.product_interface import Product
from app.core.Interfaces.receipt_repository_interface import ReceiptRepositoryInterface
from app.core.Interfaces.repository import Repository
from app.core.Interfaces.shift_repository_interface import ShiftRepositoryInterface
from app.infra.in_memory_repositories.campaign_in_memory_repository import (
    CampaignInMemoryRepository,
)
from app.infra.in_memory_repositories.product_in_memory_repository import (
    ProductInMemoryRepository,
)
from app.infra.in_memory_repositories.receipt_in_memory_repository import (
    ReceiptInMemoryRepository,
)
from app.infra.in_memory_repositories.shift_in_memory_repository import (
    ShiftInMemoryRepository,
)


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
    _exchange_rate_service: ExchangeRateService = field(
        init=False, default_factory=ExchangeRateService
    )

    def __post_init__(self) -> None:
        self._campaigns = CampaignInMemoryRepository(
            products_repo=self._products,
        )
        self._receipts = ReceiptInMemoryRepository(
            products=self._products,
            shifts=self._shifts,
            campaigns_repo=self._campaigns,
            exchange_rate_service=self._exchange_rate_service,
        )

    def products(self) -> Repository[Product]:
        return self._products

    def receipts(self) -> ReceiptRepositoryInterface:
        return self._receipts

    def campaigns(self) -> Repository[Campaign]:
        return self._campaigns

    def shifts(self) -> ShiftRepositoryInterface:
        return self._shifts
