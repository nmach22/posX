from typing import Protocol


class ICampaignDiscountCalculator(Protocol):
    def calculate_price_for_this_campaign(
        self,
        receipt_id: str,
        campaign_without_type_on_this_product: "CampaignAndProducts",
        receipt_product: "ReceiptProduct",
        receipt_repo: "ReceiptInMemoryRepository",
    ) -> int:
        pass

    def apply_discount_campaign(
        self, receipt_product: "ReceiptProduct", discount_data: "Discount"
    ) -> int:
        pass

    def apply_buy_n_get_n_campaign(
        self, receipt_product: "ReceiptProduct", buy_n_get_n_data: "BuyNGetN"
    ) -> int:
        pass

    def apply_combo_campaign(
        self,
        receipt_id: str,
        receipt_product: "ReceiptProduct",
        campaign_without_type_on_this_product: "CampaignAndProducts",
        combo_data: "Combo",
        receipt_repo: "ReceiptInMemoryRepository",
    ) -> int:
        pass
