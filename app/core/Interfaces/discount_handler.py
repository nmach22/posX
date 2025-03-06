from typing import Protocol


class DiscountHandler(Protocol):
    def calculate_discounted_price(self, old_price: int, discount: int) -> int:
        pass
