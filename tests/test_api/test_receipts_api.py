import os
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.runner.setup import setup

os.environ["REPOSITORY_KIND"] = "in_memory"


@pytest.fixture(scope="function")
def test_app() -> TestClient:
    """Create a test client with controlled repository."""
    app = setup()
    return TestClient(app)


@pytest.fixture(scope="function")
def shift_id(test_app: TestClient) -> str:
    response = test_app.post("/shifts")
    shift_id = response.json()["shift"]["shift_id"]
    return str(shift_id)


@pytest.fixture(scope="function")
def receipt_id(test_app: TestClient, shift_id: str) -> Any:
    response = test_app.post(
        "/receipts", json={"shift_id": shift_id, "currency": "USD"}
    )
    assert response.status_code == 201
    receipt_id = response.json()["receipt"]["id"]
    return str(receipt_id)


@pytest.fixture(scope="function")
def product_id(test_app: TestClient) -> Any:
    payload = {"name": "Test Product", "barcode": "123456", "price": 100}
    response = test_app.post("/products", json=payload)
    assert response.status_code == 201
    return response.json()["product"]["id"]


def test_create_receipt(test_app: TestClient, shift_id: str) -> None:
    """Test creating a new receipt"""
    response = test_app.post(
        "/receipts", json={"shift_id": shift_id, "currency": "USD"}
    )
    assert response.status_code == 201
    assert "receipt" in response.json()
    assert "id" in response.json()["receipt"]


def test_close_receipt(test_app: TestClient, receipt_id: str) -> None:
    """Test closing a receipt"""
    response = test_app.post(f"/receipts/{receipt_id}/close")
    assert response.status_code == 200
    assert response.json()["message"] == f"Receipt {receipt_id} successfully closed."


def test_close_non_existent_receipt(test_app: TestClient) -> None:
    """Should return 404 when closing a non-existent receipt"""
    response = test_app.post("/receipts/non-existent-receipt/close")
    assert response.status_code == 404


def test_add_product_to_receipt(
    test_app: TestClient, receipt_id: str, product_id: str
) -> None:
    """Test adding a product to a receipt"""
    response = test_app.post(
        f"/receipts/{receipt_id}/products",
        json={"product_id": product_id, "quantity": 2},
    )
    print(response.json())
    assert response.status_code == 201
    assert response.json()["receipt"]["products"][0]["id"] == product_id
    assert "receipt" in response.json()


def test_get_receipt(test_app: TestClient, receipt_id: str) -> None:
    """Test retrieving a receipt"""
    response = test_app.get(f"/receipts/{receipt_id}")
    assert response.status_code == 200
    assert "receipt" in response.json()


def test_calculate_payment(test_app: TestClient, receipt_id: str) -> None:
    """Test calculating payment for a receipt"""
    response = test_app.post(f"/receipts/{receipt_id}/quotes")
    assert response.status_code == 200
    assert "id" in response.json()


def test_add_payment(test_app: TestClient, receipt_id: str) -> None:
    """Test adding a payment to a receipt"""
    response = test_app.post(f"/receipts/{receipt_id}/payments")
    assert response.status_code == 200
    assert "id" in response.json()
    assert "total" in response.json()
