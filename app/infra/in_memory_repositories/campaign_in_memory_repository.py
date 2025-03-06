import uuid
from dataclasses import dataclass, field
from typing import Dict

from app.core.Interfaces.campaign_interface import BuyNGetN, Campaign, Combo, Discount
from app.core.Interfaces.product_interface import Product
from app.core.Interfaces.repository import Repository
from app.core.classes.errors import DoesntExistError
from app.infra.in_memory_repositories.product_in_memory_repository import (
    ProductInMemoryRepository,
)


@dataclass
class CampaignAndProducts:
    id: str
    campaign_id: str
    product_id: str
    discounted_price: int


@dataclass
class CampaignInMemoryRepository(Repository[Campaign]):
    products_repo: Repository[Product] = field(
        default_factory=ProductInMemoryRepository
    )
    # campaign_product_list: list[CampaignAndProducts] = field(default_factory=list)
    campaigns_product_list: Dict[str, list[CampaignAndProducts]] = field(
        default_factory=dict
    )
    campaigns: list[Campaign] = field(default_factory=list)

    def create(self, campaign: Campaign) -> Campaign:
        self.campaigns.append(campaign)
        if campaign.type == "discount" and isinstance(campaign.data, Discount):
            if self.product_does_not_exist(campaign.data.product_id):
                raise DoesntExistError
            old_price = self.products_repo.read(campaign.data.product_id).price
            discount = campaign.data.discount_percentage
            new_price = int(old_price - (old_price * discount) / 100)
            product_for_campaign = CampaignAndProducts(
                str(uuid.uuid4()),
                campaign.campaign_id,
                campaign.data.product_id,
                new_price,
            )
            if campaign.data.product_id not in self.campaigns_product_list:
                self.campaigns_product_list[campaign.data.product_id] = []
            self.campaigns_product_list[campaign.data.product_id].append(
                product_for_campaign
            )
        if campaign.type == "combo" and isinstance(campaign.data, Combo):
            for product_id in campaign.data.products:
                if self.product_does_not_exist(product_id):
                    raise DoesntExistError

            products_id_list = campaign.data.products
            for product_id in products_id_list:
                old_price = self.products_repo.read(product_id).price
                discount = campaign.data.discount_percentage
                new_price = int(old_price - (old_price * discount) / 100)
                product_for_campaign = CampaignAndProducts(
                    str(uuid.uuid4()),
                    campaign.campaign_id,
                    product_id,
                    new_price,
                )
                if product_id not in self.campaigns_product_list:
                    self.campaigns_product_list[product_id] = []
                self.campaigns_product_list[product_id].append(product_for_campaign)

        if campaign.type == "buy n get n" and isinstance(campaign.data, BuyNGetN):
            if self.product_does_not_exist(campaign.data.product_id):
                raise DoesntExistError
            product_for_campaign = CampaignAndProducts(
                str(uuid.uuid4()),
                campaign.campaign_id,
                campaign.data.product_id,
                self.products_repo.read(campaign.data.product_id).price,
            )
            if campaign.data.product_id not in self.campaigns_product_list:
                self.campaigns_product_list[campaign.data.product_id] = []
            self.campaigns_product_list[campaign.data.product_id].append(
                product_for_campaign
            )

        return campaign

    def delete(self, campaign_id: str) -> None:
        find: bool = False
        for campaign in self.campaigns:
            if campaign.campaign_id == campaign_id:
                self.campaigns.remove(campaign)
                find = True

        for product_id, campaign_product_list in list(
            self.campaigns_product_list.items()
        ):
            for campaign_product in campaign_product_list:
                if campaign_product.campaign_id == campaign_id:
                    del self.campaigns_product_list[product_id]
                    return

        if not find:
            raise DoesntExistError
        return

    def read_all(self) -> list[Campaign]:
        return self.campaigns

    def read(self, campaign_id: str) -> Campaign:
        raise NotImplementedError("Not implemented yet.")

    def update(self, campaign: Campaign) -> None:
        raise NotImplementedError("Not implemented yet.")

    def product_does_not_exist(self, product_id: str) -> bool:
        for product_from_list in self.products_repo.read_all():
            if product_from_list.id == product_id:
                return False

        return True
