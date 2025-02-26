import uuid
from dataclasses import dataclass, field

from app.core.Interfaces.campaign_interface import Campaign
from app.core.Interfaces.campaign_repository_interface import (
    CampaignRepositoryInterface,
)
from app.infra.product_in_memory_repository import (
    DoesntExistError,
    ProductInMemoryRepository,
)


@dataclass
class CampaignAndProducts:
    id: str
    campaign_id: str
    product_id: str
    discounted_price: int


@dataclass
class CampaignInMemoryRepository(CampaignRepositoryInterface):
    campaigns: list[Campaign]
    products_repo: ProductInMemoryRepository
    campaign_product_list: list[CampaignAndProducts]

    def add_campaign(self, campaign: Campaign) -> Campaign:
        self.campaigns.append(campaign)
        if campaign.type == "discount":
            old_price = self.products_repo.get_product(campaign.data.product_id).price
            discount = campaign.data.discount_percentage
            new_price = int(old_price - (old_price * discount) / 100)
            product_for_campaign = CampaignAndProducts(
                str(uuid.uuid4()),
                campaign.campaign_id,
                campaign.data.product_id,
                new_price,
            )
            self.campaign_product_list.append(product_for_campaign)
        if campaign.type == "combo":
            products_id_list = campaign.data.products
            for product_id in products_id_list:
                old_price = self.products_repo.get_product(product_id).price
                discount = campaign.data.discount_percentage
                new_price = int(old_price - (old_price * discount) / 100)
                product_for_campaign = CampaignAndProducts(
                    str(uuid.uuid4()),
                    campaign.campaign_id,
                    product_id,
                    new_price,
                )
                self.campaign_product_list.append(product_for_campaign)

        if campaign.type == "Buy n get n":
            product_for_campaign = CampaignAndProducts(
                str(uuid.uuid4()),
                campaign.campaign_id,
                campaign.data.product_id,
                self.products_repo.get_product(campaign.data.product_id).price,
            )
            self.campaign_product_list.append(product_for_campaign)

        return campaign

    def delete_campaign(self, campaign_id: str) -> None:
        find: bool = False
        for campaign in self.campaigns:
            if campaign.campaign_id == campaign_id:
                self.campaigns.remove(campaign)
                find = True

        for campaign_product in self.campaign_product_list:
            if campaign_product.campaign_id == campaign_id:
                self.campaign_product_list.remove(campaign_product)
                return

        if not find:
            raise DoesntExistError
        return

    def get_all_campaigns(self) -> list[Campaign]:
        return self.campaigns
