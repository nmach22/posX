import unittest
from typing import Dict

import pytest

from app.core.classes.campaign_service import CampaignService
from app.core.Interfaces.campaign_interface import (
    BuyNGetN,
    Campaign,
    CampaignRequest,
    Combo,
    Discount,
)
from app.core.Interfaces.product_interface import Product
from app.infra.in_memory_repositories.campaign_in_memory_repository import (
    CampaignAndProducts,
    CampaignInMemoryRepository,
)
from app.infra.in_memory_repositories.product_in_memory_repository import (
    DoesntExistError,
    ProductInMemoryRepository,
)


class TestCampaignService(unittest.TestCase):
    def test_create_campaign(self) -> None:
        campaigns: list[Campaign] = []
        campaigns_products: Dict[
            str, list[CampaignAndProducts]
        ] = {}  # Changed to dictionary
        product_repo = ProductInMemoryRepository(
            [Product("123", "sigareti", 10, "12345")]
        )
        repository = CampaignInMemoryRepository(
            product_repo, campaigns_products, campaigns
        )
        campaign_service = CampaignService(repository)
        campaign = campaign_service.create_campaign(
            CampaignRequest(
                type="discount",
                discount=Discount(product_id="123", discount_percentage=10),
            )
        )
        assert campaign.type == "discount"
        assert (
            isinstance(campaign.data, Discount)
            and campaign.data.discount_percentage == 10
        )
        assert isinstance(campaign.data, Discount) and campaign.data.product_id == "123"
        assert (
            "123" in campaigns_products
        )  # Check if product_id exists in the dictionary

    def test_delete_campaign_success(self) -> None:
        campaigns: list[Campaign] = []
        campaigns_products: Dict[
            str, list[CampaignAndProducts]
        ] = {}  # Changed to dictionary
        product_list: list[Product] = [Product("123", "sigareti", 10, "12345")]
        product_repo = ProductInMemoryRepository(product_list)
        repository = CampaignInMemoryRepository(
            product_repo, campaigns_products, campaigns
        )
        campaign_service = CampaignService(repository)
        campaign = campaign_service.create_campaign(
            CampaignRequest(
                type="discount",
                discount=Discount(product_id="123", discount_percentage=10),
            )
        )

        campaign_service.delete_campaign(campaign.campaign_id)
        assert len(repository.read_all()) == 0
        assert "123" not in campaigns_products  # Ensure the product_id is removed

    def test_delete_campaign_raises_error(self) -> None:
        campaigns: list[Campaign] = []
        campaigns_products: Dict[
            str, list[CampaignAndProducts]
        ] = {}  # Changed to dictionary
        product_repo = ProductInMemoryRepository([])
        repository = CampaignInMemoryRepository(
            product_repo, campaigns_products, campaigns
        )
        campaign_service = CampaignService(repository)

        with pytest.raises(DoesntExistError):
            campaign_service.delete_campaign("123")

    def test_read_all_campaigns(self) -> None:
        campaigns: list[Campaign] = []
        campaigns_products: Dict[
            str, list[CampaignAndProducts]
        ] = {}  # Changed to dictionary
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
                type="discount",
                discount=Discount(product_id="123", discount_percentage=10),
            )
        )
        campaign2 = campaign_service.create_campaign(
            CampaignRequest(
                type="combo",
                combo=Combo(products=["111", "123"], discount_percentage=20),
            )
        )

        campaign3 = campaign_service.create_campaign(
            CampaignRequest(
                type="buy n get n",
                buy_n_get_n=BuyNGetN(product_id="111", buy_quantity=2, get_quantity=1),
            )
        )

        returned_campaigns = campaign_service.read_all_campaigns()
        assert len(returned_campaigns) == 3
        assert returned_campaigns[0].campaign_id == campaign1.campaign_id
        assert returned_campaigns[1].campaign_id == campaign2.campaign_id
        assert returned_campaigns[2].campaign_id == campaign3.campaign_id
        assert returned_campaigns[0].type == "discount"
        assert returned_campaigns[1].type == "combo"
        assert returned_campaigns[2].type == "buy n get n"
        assert (
            isinstance(returned_campaigns[0].data, Discount)
            and returned_campaigns[0].data.discount_percentage == 10
        )
        assert (
            isinstance(returned_campaigns[1].data, Combo)
            and returned_campaigns[1].data.discount_percentage == 20
        )
        assert (
            "123" in campaigns_products
        )  # Check if product_id exists in the dictionary
        assert (
            "111" in campaigns_products
        )  # Check if product_id exists in the dictionary
