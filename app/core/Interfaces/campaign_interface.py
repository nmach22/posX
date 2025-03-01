from dataclasses import dataclass
from typing import Protocol, Union

from pydantic import BaseModel


class BuyNGetN(BaseModel):
    product_id: str
    buy_quantity: int
    get_quantity: int


class Discount(BaseModel):
    product_id: str
    discount_percentage: int


class Combo(BaseModel):
    products: list[str]
    discount_percentage: int


class ReceiptDiscount(BaseModel):
    min_amount: int
    discount_percentage: int


# Union type to accept different campaign structures
CampaignData = Union[BuyNGetN, Discount, Combo, ReceiptDiscount]


class CampaignRequest(BaseModel):
    type: str
    buy_n_get_n: BuyNGetN
    discount: Discount
    combo: Combo
    receipt_discount: ReceiptDiscount


@dataclass
class Campaign:
    campaign_id: str
    type: str
    data: CampaignData


class CampaignInterface(Protocol):
    def create_campaign(self, campaign_request: CampaignRequest) -> Campaign:
        pass

    def delete_campaign(self, campaign_id: str) -> None:
        pass

    def read_all_campaigns(self) -> list[Campaign]:
        pass
