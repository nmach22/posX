import os
import pytest
from fastapi.testclient import TestClient

from app.runner.setup import setup

os.environ["REPOSITORY_KIND"] = "in_memory"


@pytest.fixture(scope="function")
def test_app() -> TestClient:
    """Create a test client with controlled repository."""
    app = setup()
    return TestClient(app)


def test_create_shift(test_app: TestClient) -> None:
    """Test creating a new shift"""
    response = test_app.post("/shifts")
    assert response.status_code == 201
    assert "shift" in response.json()
    assert "shift_id" in response.json()["shift"]
    assert [] == response.json()["shift"]["receipts"]
    assert "open" == response.json()["shift"]["status"]


def test_get_x_reports_valid_shift(test_app: TestClient) -> None:
    """Test fetching X report for a valid shift"""
    response = test_app.post("/shifts")
    shift_id = response.json()["shift"]["shift_id"]

    response = test_app.get(f"/shifts/x-reports?shift_id={shift_id}")
    assert response.status_code == 200
    assert "x_report" in response.json()


def test_get_x_reports_non_existent_shift(test_app: TestClient) -> None:
    """Should return 404 when fetching X report for a non-existent shift"""
    response = test_app.get("/shifts/x-reports?shift_id=non-existent")
    assert response.status_code == 404
    assert response.json()["detail"] == "Shift not found."


def test_close_shift(test_app: TestClient) -> None:
    """Test closing a shift"""
    response = test_app.post("/shifts")
    shift_id = response.json()["shift"]["shift_id"]

    response = test_app.post(f"/shifts/close-shift?shift_id={shift_id}")
    assert response.status_code == 200
    assert response.json()["message"] == f"Shift {shift_id} successfully closed."


def test_close_already_closed_shift(test_app: TestClient) -> None:
    """Should return 400 when trying to close an already closed shift"""
    response = test_app.post("/shifts")
    shift_id = response.json()["shift"]["shift_id"]
    test_app.post(f"/shifts/close-shift?shift_id={shift_id}")

    response = test_app.post(f"/shifts/close-shift?shift_id={shift_id}")
    assert response.status_code == 400
    assert (
        f"Shift with id<{shift_id}> is already closed."
        in response.json()["detail"]["error"]["message"]
    )


def test_close_non_existent_shift(test_app: TestClient) -> None:
    """Should return 404 when closing a non-existent shift"""
    response = test_app.post("/shifts/close-shift?shift_id=non-existent")
    assert response.status_code == 404
    assert (
        "Shift with id<non-existent> does not exist."
        in response.json()["detail"]["error"]["message"]
    )


def test_get_sales_report(test_app: TestClient) -> None:
    """Test retrieving the sales report"""
    response = test_app.get("/shifts/sales")
    assert response.status_code == 200
    assert "total_receipts" in response.json()
    assert "total_revenue" in response.json()
    assert isinstance(response.json()["closed_receipts"], list)
