from copy import deepcopy
from dataclasses import dataclass, field

from app.core.classes.errors import DoesntExistError
from app.core.classes.exchange_rate_service import ExchangeRateService
from app.core.classes.percentage_discount import PercentageDiscount
from app.core.Interfaces.campaign_interface import (
    BuyNGetN,
    Campaign,
    Combo,
    Discount,
    ReceiptDiscount,
)
from app.core.Interfaces.discount_handler import DiscountHandler
from app.core.Interfaces.receipt_interface import (
    AddProductRequest,
    Receipt,
    ReceiptForPayment,
    ReceiptProduct,
)
from app.core.Interfaces.receipt_repository_interface import ReceiptRepositoryInterface
from app.infra.in_memory_repositories.campaign_in_memory_repository import (
    CampaignAndProducts,
    CampaignInMemoryRepository,
)
from app.infra.in_memory_repositories.product_in_memory_repository import (
    ProductInMemoryRepository,
)
from app.infra.in_memory_repositories.shift_in_memory_repository import (
    ShiftInMemoryRepository,
)


@dataclass
class ReceiptInMemoryRepository(ReceiptRepositoryInterface):
    receipts: list[Receipt] = field(default_factory=list)
    products: ProductInMemoryRepository = field(
        default_factory=ProductInMemoryRepository
    )
    shifts: ShiftInMemoryRepository = field(default_factory=ShiftInMemoryRepository)
    campaigns_repo: CampaignInMemoryRepository = field(
        default_factory=CampaignInMemoryRepository
    )
    exchange_rate_service: ExchangeRateService = field(
        default_factory=ExchangeRateService
    )
    discount_handler: DiscountHandler = field(default_factory=PercentageDiscount)

    def create(self, receipt: Receipt) -> Receipt:
        shift_found = False
        for shift in self.shifts.read_all_shifts():
            if shift.shift_id == receipt.shift_id:
                shift_found = True
                break

        if shift_found is False:
            raise (
                DoesntExistError(f"Shift with ID {receipt.shift_id} does not exist.")
            )

        self.receipts.append(deepcopy(receipt))
        self.shifts.add_receipt_to_shift(receipt)
        return receipt

    def update(self, updated_receipt: Receipt) -> None:
        for receipt in self.receipts:
            if receipt.id == updated_receipt.id:
                self.receipts.remove(receipt)
                self.receipts.append(updated_receipt)
                return
            raise DoesntExistError(f"Receipt with ID {receipt.id} does not exist.")

    def read(self, receipt_id: str) -> Receipt:
        for receipt in self.receipts:
            if receipt.id == receipt_id:
                #    receipt.discounted_total = self.calculate_payment(receipt.id)
                return receipt
        raise DoesntExistError(f"Receipt with ID {receipt_id} does not exist.")

    def add_product_to_receipt(
        self, receipt_id: str, product_request: AddProductRequest
    ) -> Receipt:
        product_price = 0
        product_found = False
        for product in self.products.read_all():
            if product.id == product_request.product_id:
                product_price = product.price
                product_found = True
                break

        if product_found is False:
            raise (
                DoesntExistError(
                    f"Product with ID {product_request.product_id} does not exist."
                )
            )

        for receipt in self.receipts:
            if receipt.id == receipt_id:
                total_price = product_request.quantity * product_price

                new_product = ReceiptProduct(
                    id=product_request.product_id,
                    quantity=product_request.quantity,
                    price=product_price,
                    total=total_price,
                )

                receipt.products.append(deepcopy(new_product))
                receipt.total += total_price

                return receipt
        raise DoesntExistError(f"Receipt with ID {receipt_id} does not exist.")

    def calculate_payment(
        self,
        receipt_id: str,
    ) -> ReceiptForPayment:
        discounted_price: int = 0
        receipt = self.read(receipt_id)
        receipt_products_from_receipt = receipt.products
        campaigns_and_products = self.campaigns_repo.campaigns_product_list
        for receipt_product in receipt_products_from_receipt:
            campaigns_list_on_this_product: list[CampaignAndProducts] = (
                campaigns_and_products[receipt_product.id]
            )
            if campaigns_list_on_this_product is None:
                discounted_price += receipt_product.total
            else:
                best_discounted_price_for_this_product = receipt_product.total
                for (
                    campaign_without_type_on_this_product
                ) in campaigns_list_on_this_product:
                    discounted_price_using_this_campaign = (
                        self.calculate_price_for_this_campaign(
                            receipt_id,
                            campaign_without_type_on_this_product,
                            receipt_product,
                        )
                    )
                    if (
                        discounted_price_using_this_campaign
                        < best_discounted_price_for_this_product
                    ):
                        best_discounted_price_for_this_product = (
                            discounted_price_using_this_campaign
                        )

                discounted_price += best_discounted_price_for_this_product

        for campaign in self.campaigns_repo.campaigns:
            if (
                campaign.type == "receipt discount"
                and isinstance(campaign.data, ReceiptDiscount)
                and discounted_price >= campaign.data.min_amount
            ):
                discounted_price = self.discount_handler.calculate_discounted_price(
                    discounted_price, campaign.data.discount_percentage
                )
                break

        total_price = receipt.total
        if receipt.currency != "GEL":
            conversion_rate = self.exchange_rate_service.get_exchange_rate(
                "GEL", receipt.currency
            )
            discounted_price = int(discounted_price * conversion_rate)
            total_price = int(total_price * conversion_rate)

        receipt.discounted_total = discounted_price
        self.shifts.add_receipt_to_shift(receipt)

        return ReceiptForPayment(
            receipt, discounted_price, total_price - discounted_price
        )

    def calculate_price_for_this_campaign(
        self,
        receipt_id: str,
        campaign_without_type_on_this_product: CampaignAndProducts,
        receipt_product: ReceiptProduct,
    ) -> int:
        campaign_with_type_on_this_product = self.get_campaign_with_campaign_id(
            campaign_without_type_on_this_product.campaign_id
        )
        discounted_price: int = receipt_product.total
        if (
            isinstance(campaign_with_type_on_this_product, Campaign)
            and campaign_with_type_on_this_product.type == "discount"
            and isinstance(campaign_with_type_on_this_product.data, Discount)
        ):
            discounted_price = self.discount_handler.calculate_discounted_price(
                receipt_product.total,
                campaign_with_type_on_this_product.data.discount_percentage,
            )
        elif (
            isinstance(campaign_with_type_on_this_product, Campaign)
            and campaign_with_type_on_this_product.type == "buy n get n"
            and isinstance(campaign_with_type_on_this_product.data, BuyNGetN)
        ):
            n = campaign_with_type_on_this_product.data.buy_quantity
            m = campaign_with_type_on_this_product.data.get_quantity
            amount_of_campaign_costumer_use = receipt_product.quantity // (n + m)
            amount_of_product_got_without_price = m * amount_of_campaign_costumer_use

            discounted_price = receipt_product.total - (
                receipt_product.price * amount_of_product_got_without_price
            )
        elif (
            isinstance(campaign_with_type_on_this_product, Campaign)
            and campaign_with_type_on_this_product.type == "combo"
            and isinstance(campaign_with_type_on_this_product.data, Combo)
        ):
            other_products_in_combo = self.get_other_products_with_same_campaign(
                campaign_without_type_on_this_product.campaign_id
            )
            other_products_in_combo.remove(
                campaign_without_type_on_this_product.product_id
            )
            combo_failed = False

            for next_product_id_in_combo in other_products_in_combo:
                if self.product_not_in_receipt(next_product_id_in_combo, receipt_id):
                    combo_failed = True
                    break

            if combo_failed:
                discounted_price = receipt_product.total
            else:
                discount_percentage = (
                    campaign_with_type_on_this_product.data.discount_percentage
                )
                discounted_price = self.discount_handler.calculate_discounted_price(
                    receipt_product.total,
                    discount_percentage,
                )

        return discounted_price

    def add_payment(
        self,
        receipt_id: str,
    ) -> ReceiptForPayment:
        receipt_for_payment = self.calculate_payment(receipt_id)
        self.shifts.add_receipt_to_shift(receipt_for_payment.receipt)
        return receipt_for_payment

    def delete(self, receipt_id: str) -> None:
        raise NotImplementedError("Not implemented yet.")

    def read_all(self) -> list[Receipt]:
        raise NotImplementedError("Not implemented yet.")

    def get_campaign_with_campaign_id(self, campaign_id: str) -> Campaign | None:
        for campaign in self.campaigns_repo.campaigns:
            if campaign.campaign_id == campaign_id:
                return campaign

        return None

    def get_other_products_with_same_campaign(self, campaign_id: str) -> list[str]:
        result_list: list[str] = []
        for (
            product_id,
            campaign_product_list,
        ) in self.campaigns_repo.campaigns_product_list.items():
            for campaign_product in campaign_product_list:
                if campaign_product.campaign_id == campaign_id:
                    result_list.append(product_id)

        return result_list

    def product_not_in_receipt(self, product_id: str, receipt_id: str) -> bool:
        receipt = self.read(receipt_id)
        receipt_products_from_receipt = receipt.products
        for receipt_product in receipt_products_from_receipt:
            if receipt_product.id == product_id:
                return False
        return True
