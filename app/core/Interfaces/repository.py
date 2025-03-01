from typing import TypeVar, Protocol

ItemT = TypeVar("ItemT")


class Repository(Protocol[ItemT]):
    def create(self, item: ItemT) -> ItemT:
        pass

    def read(self, item_id: str) -> ItemT:
        pass

    def update(self, item: ItemT) -> None:
        pass

    def delete(self, item_id: str) -> None:
        pass

    def read_all(self) -> list[ItemT]:
        pass