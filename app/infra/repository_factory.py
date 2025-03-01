import os
import sqlite3

from dotenv import load_dotenv

from app.infra.in_memory import InMemory
from app.infra.sqlite import Sqlite

load_dotenv()  # Load environment variables from .env


class RepositoryFactory:
    @staticmethod
    def create():
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
