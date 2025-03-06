from app.core.Interfaces.discount_handler import DiscountHandler


class PercentageDiscount(DiscountHandler):
    def calculate_discounted_price(self, old_price: int, discount: int) -> int:
        new_price = old_price - int(old_price * discount / 100)
        return new_price
