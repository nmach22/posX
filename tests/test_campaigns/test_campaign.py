import unittest

import pytest

from app.core.Interfaces.campaign_interface import (
    Campaign,
    CampaignRequest,
    Discount,
    Combo,
    BuyNGetN,
)
from app.core.Interfaces.product_interface import Product

from app.core.classes.campaign_service import CampaignService
from app.infra.campaign_in_memory_repository import (
    CampaignInMemoryRepository,
    CampaignAndProducts,
)
from app.infra.product_in_memory_repository import (
    DoesntExistError,
    ProductInMemoryRepository,
)


class TestCampaignService(unittest.TestCase):
    def test_create_campaign(self):
        campaigns: list[Campaign] = []
        campaigns_products: list[CampaignAndProducts] = []
        product_repo = ProductInMemoryRepository(
            [Product("123", "sigareti", 10, "12345")]
        )
        repository = CampaignInMemoryRepository(
            product_repo, campaigns_products, campaigns
        )
        campaign_service = CampaignService(repository)
        campaign = campaign_service.create_campaign(
            CampaignRequest(
                type="discount", data=Discount(product_id="123", discount_percentage=10)
            )
        )
        assert campaign.type == "discount"
        assert campaign.data.discount_percentage == 10
        assert campaign.data.product_id == "123"

    def test_delete_campaign_success(self):
        campaigns: list[Campaign] = []
        campaigns_products: list[CampaignAndProducts] = []
        product_list: list[Product] = [Product("123", "sigareti", 10, "12345")]
        product_repo = ProductInMemoryRepository(product_list)
        repository = CampaignInMemoryRepository(
            product_repo, campaigns_products, campaigns
        )
        campaign_service = CampaignService(repository)
        campaign = campaign_service.create_campaign(
            CampaignRequest(
                type="discount", data=Discount(product_id="123", discount_percentage=10)
            )
        )

        campaign_service.delete_campaign(campaign.campaign_id)
        assert len(repository.get_all_campaigns()) == 0

    def test_delete_campaign_raises_error(self):
        campaigns: list[Campaign] = []
        campaigns_products: list[CampaignAndProducts] = []
        product_repo = ProductInMemoryRepository([])
        repository = CampaignInMemoryRepository(
            product_repo, campaigns_products, campaigns
        )
        campaign_service = CampaignService(repository)

        with pytest.raises(DoesntExistError):
            campaign_service.delete_campaign("123")

    def test_read_all_campaigns(self):
        campaigns: list[Campaign] = []
        campaigns_products: list[CampaignAndProducts] = []
        product_list: list[Product] = [
            Product("123", "sigareti", 10, "12345"),
            Product("111", "kvercxi", 5, "123123"),
        ]
        product_repo = ProductInMemoryRepository(product_list)
        repository = CampaignInMemoryRepository(
            product_repo, campaigns_products, campaigns
        )
        campaign_service = CampaignService(repository)
        campaign1 = campaign_service.create_campaign(
            CampaignRequest(
                type="discount", data=Discount(product_id="123", discount_percentage=10)
            )
        )
        campaign2 = campaign_service.create_campaign(
            CampaignRequest(
                type="combo",
                data=Combo(products=["111", "123"], discount_percentage=20),
            )
        )

        campaign3 = campaign_service.create_campaign(
            CampaignRequest(
                type="Buy n get n",
                data=BuyNGetN(product_id="111", buy_quantity=2, get_quantity=1),
            )
        )

        returned_campaigns = campaign_service.read_all_campaigns()
        assert len(returned_campaigns) == 3
        assert returned_campaigns[0].campaign_id == campaign1.campaign_id
        assert returned_campaigns[1].campaign_id == campaign2.campaign_id
        assert returned_campaigns[2].campaign_id == campaign3.campaign_id
        assert returned_campaigns[0].type == "discount"
        assert returned_campaigns[1].type == "combo"
        assert returned_campaigns[2].type == "Buy n get n"
        assert returned_campaigns[0].data.discount_percentage == 10
        assert returned_campaigns[1].data.discount_percentage == 20
