import os

from app.infra.in_memory import InMemory
from app.infra.sqlite import Sqlite


class RepositoryFactory:
    @staticmethod
    def create():
        """Creates the appropriate repository based on the environment variable."""
        repository_kind = os.getenv("REPOSITORY_KIND")
        print(repository_kind)

        if repository_kind == "sqlite-memory":
            print("Using SQLite (in-memory)")
            return Sqlite(":memory:")
        elif repository_kind == "sqlite-disk":
            print("Using SQLite (persistent)")
            return Sqlite("pos.db")
        else:
            print("Using InMemory repository")
            return InMemory()
