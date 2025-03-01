import sqlite3

from app.core.Interfaces.campaign_repository_interface import (
    CampaignRepositoryInterface,
)
from app.core.Interfaces.product_repository_interface import ProductRepositoryInterface
from app.core.Interfaces.receipt_repository_interface import ReceiptRepositoryInterface
from app.core.Interfaces.shift_repository_interface import ShiftRepositoryInterface
from app.infra.sql_repositories.campaign_sql_repository import CampaignSQLRepository
from app.infra.sql_repositories.product_sql_repository import ProductSQLRepository
from app.infra.sql_repositories.receipt_sql_repository import ReceiptSQLRepository
from app.infra.sql_repositories.shift_sql_repository import ShiftSQLRepository


# @dataclass
class Sqlite:
    # db_path: str
    def __init__(self, connection: sqlite3.Connection):
        """Initialize repositories with correct dependencies."""
        self._products = ProductSQLRepository(connection)
        self._campaigns = CampaignSQLRepository(connection, self._products)
        self._shifts = ShiftSQLRepository(connection, self._products)
        self._receipts = ReceiptSQLRepository(
            connection, self._products, self._shifts, self._campaigns
        )

    def products(self) -> ProductRepositoryInterface:
        return self._products

    def shifts(self) -> ShiftRepositoryInterface:
        return self._shifts

    def receipts(self) -> ReceiptRepositoryInterface:
        return self._receipts

    def campaigns(self) -> CampaignRepositoryInterface:
        return self._campaigns
