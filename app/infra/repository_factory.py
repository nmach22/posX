import os
import sqlite3
from typing import Protocol

from dotenv import load_dotenv

from app.core.Interfaces.campaign_interface import Campaign
from app.core.Interfaces.product_interface import Product
from app.core.Interfaces.receipt_repository_interface import ReceiptRepositoryInterface
from app.core.Interfaces.repository import Repository
from app.core.Interfaces.shift_repository_interface import ShiftRepositoryInterface
from app.infra.in_memory import InMemory
from app.infra.sqlite import Sqlite

load_dotenv()  # Load environment variables from .env


class RepositoryProvider(Protocol):
    def products(self) -> Repository[Product]:
        pass

    def shifts(self) -> ShiftRepositoryInterface:
        pass

    def receipts(self) -> ReceiptRepositoryInterface:
        pass

    def campaigns(self) -> Repository[Campaign]:
        pass


class RepositoryFactory:
    @staticmethod
    def create() -> RepositoryProvider:
        """Creates the appropriate repository based on the environment variable."""
        repository_kind = os.getenv("REPOSITORY_KIND")

        if repository_kind == "sqlite-memory":
            print("Using SQLite (in-memory)")
            return Sqlite(sqlite3.connect(":memory:", check_same_thread=False))
        elif repository_kind == "sqlite-disk":
            print("Using SQLite (persistent)")
            return Sqlite(sqlite3.connect("pos.db", check_same_thread=False))
        else:
            print("Using InMemory repository")
            return InMemory()
