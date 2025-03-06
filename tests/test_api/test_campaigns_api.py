import os
import uuid

import pytest
from starlette.testclient import TestClient

from app.runner.setup import setup

os.environ["REPOSITORY_KIND"] = "in_memory"


@pytest.fixture(scope="function")
def test_app() -> TestClient:
    """Create a test client with controlled repository."""
    app = setup()
    return TestClient(app)


@pytest.fixture(scope="function")
def create_product(test_app: TestClient) -> str:
    barcode = uuid.uuid4()
    payload = {"name": "Test Product", "barcode": str(barcode), "price": 100}
    response = test_app.post("/products", json=payload)
    assert response.status_code == 201
    return response.json()["product"]["id"]


def test_get_all_products(test_app: TestClient) -> None:
    response = test_app.get("/campaigns")
    assert response.status_code == 200
    assert "campaigns" in response.json()
    assert isinstance(response.json()["campaigns"], list)


def test_create_buy_n_get_n_campaign(test_app: TestClient, create_product: str) -> None:
    """Test creating a buy n get n campaign using a created product."""
    product_id = create_product

    payload_campaign = {
        "type": "buy n get n",
        "buy_n_get_n": {"product_id": product_id, "buy_quantity": 2, "get_quantity": 1},
    }
    response_campaign = test_app.post("/campaigns", json=payload_campaign)

    print(response_campaign.json())
    assert response_campaign.status_code == 201
    assert response_campaign.json()["campaign"]["type"] == "buy n get n"
    assert response_campaign.json()["campaign"]["data"]["product_id"] == product_id
    assert response_campaign.json()["campaign"]["data"]["buy_quantity"] == 2
    assert response_campaign.json()["campaign"]["data"]["get_quantity"] == 1


def test_create_discount_campaign(test_app: TestClient, create_product: str) -> None:
    """Test creating a discount campaign using a created product."""
    product_id = create_product

    payload_campaign = {
        "type": "discount",
        "discount": {"product_id": product_id, "discount_percentage": 10},
    }
    response_campaign = test_app.post("/campaigns", json=payload_campaign)

    assert response_campaign.status_code == 201
    assert response_campaign.json()["campaign"]["type"] == "discount"
    assert response_campaign.json()["campaign"]["data"]["product_id"] == product_id
    assert response_campaign.json()["campaign"]["data"]["discount_percentage"] == 10


def test_create_combo_campaign(test_app: TestClient, create_product: str) -> None:
    """Test creating a combo campaign using created products."""
    product_id1 = create_product
    product_id2 = create_product

    payload_campaign = {
        "type": "combo",
        "combo": {
            "products": [product_id1, product_id2],
            "discount_percentage": 15,
        },
    }
    response_campaign = test_app.post("/campaigns", json=payload_campaign)

    assert response_campaign.status_code == 201
    assert response_campaign.json()["campaign"]["type"] == "combo"
    assert response_campaign.json()["campaign"]["data"]["products"] == [
        product_id1,
        product_id2,
    ]
    assert response_campaign.json()["campaign"]["data"]["discount_percentage"] == 15


def test_create_campaign_missing_product(test_app: TestClient) -> None:
    payload_campaign = {
        "type": "discount",
        "discount": {
            "product_id": "non-existent-product-id",
            "discount_percentage": 10,
        },
    }
    response_campaign = test_app.post("/campaigns", json=payload_campaign)

    assert response_campaign.status_code == 404
    error_detail = response_campaign.json()["detail"]["error"]
    assert error_detail["message"] == "product with this id does not exist."


def test_delete_nonexistent_campaign(test_app: TestClient, create_product: str) -> None:
    campaign_id = "non-existent-campaign-id"
    response_fetch = test_app.delete(f"/campaigns/{campaign_id}")
    assert response_fetch.status_code == 404
    error_detail = response_fetch.json()["detail"]["error"]
    assert error_detail["message"] == "campaign with this id does not exist."


def test_delete_campaign(test_app: TestClient, create_product: str) -> None:
    product_id = create_product

    payload_campaign = {
        "type": "buy n get n",
        "buy_n_get_n": {"product_id": product_id, "buy_quantity": 2, "get_quantity": 1},
    }
    response_campaign = test_app.post("/campaigns", json=payload_campaign)

    assert response_campaign.status_code == 201
    campaign_id = response_campaign.json()["campaign"]["campaign_id"]

    response_delete = test_app.delete(f"/campaigns/{campaign_id}")

    assert response_delete.status_code == 200
    assert response_delete.json() == {}

    response_fetch = test_app.delete(f"/campaigns/{campaign_id}")
    assert response_fetch.status_code == 404
    error_detail = response_fetch.json()["detail"]["error"]
    assert error_detail["message"] == "campaign with this id does not exist."


def test_get_all_campaigns(test_app: TestClient, create_product: str) -> None:
    product_id = create_product

    payload_campaign_1 = {
        "type": "buy n get n",
        "buy_n_get_n": {"product_id": product_id, "buy_quantity": 2, "get_quantity": 1},
    }
    response_campaign_1 = test_app.post("/campaigns", json=payload_campaign_1)
    assert response_campaign_1.status_code == 201
    campaign_id_1 = response_campaign_1.json()["campaign"]["campaign_id"]

    payload_campaign_2 = {
        "type": "discount",
        "discount": {"product_id": product_id, "discount_percentage": 10},
    }
    response_campaign_2 = test_app.post("/campaigns", json=payload_campaign_2)
    assert response_campaign_2.status_code == 201
    campaign_id_2 = response_campaign_2.json()["campaign"]["campaign_id"]

    payload_campaign_3 = {
        "type": "combo",
        "combo": {
            "products": [product_id, product_id],
            "discount_percentage": 15,
        },
    }
    response_campaign_3 = test_app.post("/campaigns", json=payload_campaign_3)
    assert response_campaign_3.status_code == 201
    campaign_id_3 = response_campaign_3.json()["campaign"]["campaign_id"]

    response_get_all = test_app.get("/campaigns")
    assert response_get_all.status_code == 200

    campaigns = response_get_all.json()["campaigns"]

    assert len(campaigns) == 3
    campaign_ids = [campaign["campaign_id"] for campaign in campaigns]
    assert campaign_id_1 in campaign_ids
    assert campaign_id_2 in campaign_ids
    assert campaign_id_3 in campaign_ids
