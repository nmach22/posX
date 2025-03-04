import os

import pytest
from starlette.testclient import TestClient

from app.runner.setup import setup


os.environ["REPOSITORY_KIND"] = "in_memory"


@pytest.fixture(scope="module")
def test_app() -> TestClient:
    """Create a test client with controlled repository."""
    app = setup()
    return TestClient(app)


@pytest.fixture(scope="module")
def create_product(test_app: TestClient):
    """Fixture to create a product and return its ID."""
    payload = {"name": "Test Product", "barcode": "123456", "price": 100}
    response = test_app.post("/products", json=payload)
    assert response.status_code == 201
    return response.json()["product"]["id"]


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
    product_id = create_product

    payload_campaign = {
        "type": "combo",
        "combo": {
            "products": [product_id, "another-product-id"],
            "discount_percentage": 15,
        },
    }
    response_campaign = test_app.post("/campaigns", json=payload_campaign)

    assert response_campaign.status_code == 201
    assert response_campaign.json()["campaign"]["type"] == "combo"
    assert response_campaign.json()["campaign"]["data"]["products"] == [
        product_id,
        "another-product-id",
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
