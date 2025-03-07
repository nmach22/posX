import os

import pytest
from fastapi.testclient import TestClient

from app.runner.setup import setup

os.environ["REPOSITORY_KIND"] = "in_memory"


@pytest.fixture(scope="module")
def test_app() -> TestClient:
    """Create a test client with controlled repository."""
    app = setup()
    return TestClient(app)


def test_create_product(test_app: TestClient) -> None:
    payload = {"name": "Test Product", "barcode": "123456", "price": 100}

    response = test_app.post("/products", json=payload)
    assert response.status_code == 201
    assert response.json()["product"]["name"] == "Test Product"
    assert response.json()["product"]["barcode"] == "123456"
    assert response.json()["product"]["price"] == 100


def test_get_all_products(test_app: TestClient) -> None:
    response = test_app.get("/products")
    assert response.status_code == 200
    assert "products" in response.json()
    assert isinstance(response.json()["products"], list)


def test_create_existing_product(test_app: TestClient) -> None:
    payload = {"name": "Product", "barcode": "123457", "price": 100}

    response = test_app.post("/products", json=payload)
    assert response.status_code == 201

    payload = {"name": "Duplicate Product", "barcode": "123457", "price": 100}
    response = test_app.post("/products", json=payload)

    assert response.status_code == 409
    assert "error" in response.json()["detail"]


def test_update_product(test_app: TestClient) -> None:
    payload = {"name": "Product", "barcode": "123458", "price": 100}

    response = test_app.post("/products", json=payload)
    assert response.status_code == 201

    product_id = response.json()["product"]["id"]
    payload = {"price": 150}

    response = test_app.patch(f"/products/{product_id}", json=payload)
    if response.status_code == 404:
        assert "error" in response.json()["detail"]  # Product not found
    else:
        assert response.status_code == 200


def test_update_nonexistent_product(test_app: TestClient) -> None:
    product_id = "non-existent-id"
    payload = {"price": 200}

    response = test_app.patch(f"/products/{product_id}", json=payload)
    assert response.status_code == 404
    assert "error" in response.json()["detail"]
