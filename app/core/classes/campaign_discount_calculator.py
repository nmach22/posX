from app.core.Interfaces.campaign_discount_calculator_interface import (
    ICampaignDiscountCalculator,
)
from app.core.Interfaces.campaign_interface import Discount, BuyNGetN, Combo
from app.core.Interfaces.discount_handler import DiscountHandler
from app.core.Interfaces.receipt_interface import ReceiptProduct
from app.core.Interfaces.receipt_repository_interface import ReceiptRepositoryInterface
from app.infra.in_memory_repositories.campaign_in_memory_repository import (
    CampaignAndProducts,
)


class CampaignDiscountCalculator(ICampaignDiscountCalculator):
    discount_handler: DiscountHandler

    def __init__(self, discount_handler: DiscountHandler):
        self.discount_handler = discount_handler

    def calculate_price_for_this_campaign(
        self,
        receipt_id: str,
        campaign_without_type_on_this_product: CampaignAndProducts,
        receipt_product: ReceiptProduct,
        # todo:  change this
        receipt_repo: ReceiptRepositoryInterface,
    ) -> int:
        campaign = receipt_repo.get_campaign_with_campaign_id(
            campaign_without_type_on_this_product.campaign_id
        )

        if campaign is None:
            return receipt_product.total

        if campaign.type == "discount" and isinstance(campaign.data, Discount):
            return self.apply_discount_campaign(receipt_product, campaign.data)

        if campaign.type == "buy n get n" and isinstance(campaign.data, BuyNGetN):
            return self.apply_buy_n_get_n_campaign(receipt_product, campaign.data)

        if campaign.type == "combo" and isinstance(campaign.data, Combo):
            return self.apply_combo_campaign(
                receipt_id,
                receipt_product,
                campaign_without_type_on_this_product,
                campaign.data,
                receipt_repo,
            )

        return receipt_product.total

    def apply_discount_campaign(
        self, receipt_product: ReceiptProduct, discount_data: Discount
    ) -> int:
        return self.discount_handler.calculate_discounted_price(
            receipt_product.total, discount_data.discount_percentage
        )

    def apply_buy_n_get_n_campaign(
        self, receipt_product: ReceiptProduct, buy_n_get_n_data: BuyNGetN
    ) -> int:
        n = buy_n_get_n_data.buy_quantity
        m = buy_n_get_n_data.get_quantity
        amount_of_campaign_usage = receipt_product.quantity // (n + m)
        amount_of_free_products = m * amount_of_campaign_usage

        return receipt_product.total - (receipt_product.price * amount_of_free_products)

    def apply_combo_campaign(
        self,
        receipt_id: str,
        receipt_product: ReceiptProduct,
        campaign_without_type_on_this_product: CampaignAndProducts,
        combo_data: Combo,
        receipt_repo: ReceiptRepositoryInterface,
    ) -> int:
        other_products_in_combo = receipt_repo.get_other_products_with_same_campaign(
            campaign_without_type_on_this_product.campaign_id
        )
        other_products_in_combo.remove(campaign_without_type_on_this_product.product_id)

        for next_product_id in other_products_in_combo:
            if receipt_repo.product_not_in_receipt(next_product_id, receipt_id):
                return receipt_product.total  # Combo failed

        return self.discount_handler.calculate_discounted_price(
            receipt_product.total, combo_data.discount_percentage
        )
