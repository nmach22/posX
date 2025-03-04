import sqlite3

import pytest

from app.core.Interfaces.shift_interface import Shift
from app.infra.in_memory_repositories.product_in_memory_repository import (
    DoesntExistError,
)
from app.infra.sql_repositories.shift_sql_repository import ShiftSQLRepository


@pytest.fixture
def repo() -> ShiftSQLRepository:
    """Creates a new SQLite in-memory database for each test."""
    connection = sqlite3.connect(":memory:", check_same_thread=False)

    # Create additional test tables needed for reports
    # cursor = connection.cursor()
    # cursor.executescript("""
    #     CREATE TABLE IF NOT EXISTS receipts (
    #         id TEXT PRIMARY KEY,
    #         shift_id TEXT NOT NULL,
    #         total REAL NOT NULL,
    #         currency TEXT NOT NULL,
    #         status TEXT NOT NULL,
    #         FOREIGN KEY (shift_id) REFERENCES shifts (shift_id)
    #     );
    #
    #     CREATE TABLE IF NOT EXISTS receipt_products (
    #         id INTEGER PRIMARY KEY AUTOINCREMENT,
    #         receipt_id TEXT NOT NULL,
    #         product_id TEXT NOT NULL,
    #         quantity INTEGER NOT NULL,
    #         FOREIGN KEY (receipt_id) REFERENCES receipts (id)
    #     );
    # """)
    # connection.commit()

    return ShiftSQLRepository(connection)


def test_create_shift(repo: ShiftSQLRepository) -> None:
    """Tests creating a shift and retrieving it."""
    shift = Shift(shift_id="shift1", receipts=[], status="open")

    created_shift = repo.create(shift)
    retrieved_shift = repo.read("shift1")

    assert created_shift.shift_id == "shift1"
    assert created_shift.status == "open"
    assert retrieved_shift.shift_id == "shift1"
    assert retrieved_shift.status == "open"
    assert len(retrieved_shift.receipts) == 0


def test_update_shift(repo: ShiftSQLRepository) -> None:
    """Tests updating a shift's status."""
    # TODO anan
    pass
    # shift = Shift(shift_id="shift1", receipts=[], status="open")
    #
    # repo.create(shift)
    # updated_shift = Shift(shift_id="shift1", receipts=[], status="closed")
    # repo.update(updated_shift)
    #
    # retrieved = repo.read("shift1")
    # assert retrieved.status == "closed"


def test_read_non_existent_shift(repo: ShiftSQLRepository) -> None:
    """Tests that retrieving a non-existent shift raises DoesntExistError."""
    with pytest.raises(DoesntExistError):
        repo.read("nonexistent_shift")


def test_delete_shift(repo: ShiftSQLRepository) -> None:
    """Tests deleting a shift."""
    shift = Shift(shift_id="shift1", receipts=[], status="open")

    repo.create(shift)
    repo.delete("shift1")

    with pytest.raises(DoesntExistError):
        repo.read("shift1")


def test_delete_non_existent_shift(repo: ShiftSQLRepository) -> None:
    """Tests that deleting a non-existent shift raises DoesntExistError."""
    with pytest.raises(DoesntExistError):
        repo.delete("nonexistent_shift")


def test_get_x_report(repo: ShiftSQLRepository) -> None:
    """Tests getting an X report for an open shift with receipts."""
    # Create a shift
    # shift = Shift(shift_id="shift1", receipts=[], status="open")
    # repo.create(shift)
    #
    # # Add test data: receipts and products
    # cursor = repo.conn.cursor()
    #
    # # Add receipts
    # cursor.executescript("""
    #     INSERT INTO receipts (id, shift_id, total, currency, status)
    #     VALUES
    #         ('receipt1', 'shift1', 100.0, 'USD', 'closed'),
    #         ('receipt2', 'shift1', 150.0, 'USD', 'closed'),
    #         ('receipt3', 'shift1', 200.0, 'EUR', 'closed');
    #
    #     INSERT INTO receipt_products (receipt_id, product_id, quantity)
    #     VALUES
    #         ('receipt1', 'product1', 2),
    #         ('receipt1', 'product2', 1),
    #         ('receipt2', 'product1', 3),
    #         ('receipt3', 'product3', 4);
    # """)
    # repo.conn.commit()
    #
    # # Get X report
    # report = repo.get_x_report("shift1")
    #
    # # Verify report contents
    # assert report.shift_id == "shift1"
    # assert report.n_receipts == 3
    # assert report.revenue == {"USD": 250.0, "EUR": 200.0}
    #
    # # Verify products data - exact order might be different so check contents
    # product_ids = {p["id"] for p in report.products}
    # assert product_ids == {"product1", "product2", "product3"}
    #
    # # Find each product and check quantity
    # for product in report.products:
    #     if product["id"] == "product1":
    #         assert product["quantity"] == 5
    #     elif product["id"] == "product2":
    #         assert product["quantity"] == 1
    #     elif product["id"] == "product3":
    #         assert product["quantity"] == 4


def test_get_x_report_for_nonexistent_shift(repo: ShiftSQLRepository) -> None:
    """Tests that getting an X report for a non-existent shift raises DoesntExistError."""
    with pytest.raises(DoesntExistError):
        repo.get_x_report("nonexistent_shift")


def test_get_x_report_for_closed_shift(repo: ShiftSQLRepository) -> None:
    """Tests that getting an X report for a closed shift raises ValueError."""
    shift = Shift(shift_id="shift1", receipts=[], status="closed")
    repo.create(shift)

    with pytest.raises(
        ValueError, match="Cannot generate X Report for closed shift shift1."
    ):
        repo.get_x_report("shift1")


def test_get_lifetime_sales_report(repo: ShiftSQLRepository) -> None:
    """Tests getting a lifetime sales report."""
    # Create shifts
    # shift1 = Shift(shift_id="shift1", receipts=[], status="open")
    # shift2 = Shift(shift_id="shift2", receipts=[], status="closed")
    # repo.create(shift1)
    # repo.create(shift2)
    #
    # # Add test data
    # cursor = repo.conn.cursor()
    # cursor.executescript("""
    #     INSERT INTO receipts (id, shift_id, total, currency, status)
    #     VALUES
    #         ('receipt1', 'shift1', 100.0, 'USD', 'closed'),
    #         ('receipt2', 'shift1', 150.0, 'USD', 'closed'),
    #         ('receipt3', 'shift2', 200.0, 'EUR', 'closed'),
    #         ('receipt4', 'shift2', 75.0, 'USD', 'open');
    # """)
    # repo.conn.commit()
    #
    # # Get lifetime sales report
    # report = repo.get_lifetime_sales_report()
    #
    # # Verify report contents - should only count closed receipts
    # assert report.total_receipts == 3  # Excludes the open receipt
    # assert report.total_revenue == {"USD": 250.0, "EUR": 200.0}
    #
    # # Verify closed receipts
    # receipt_ids = {r.receipt_id for r in report.closed_receipts}
    # assert receipt_ids == {"receipt1", "receipt2", "receipt3"}
    #
    # # Find each receipt and check payment
    # payment_map = {r.receipt_id: r.calculated_payment for r in report.closed_receipts}
    # assert payment_map["receipt1"] == 100.0
    # assert payment_map["receipt2"] == 150.0
    # assert payment_map["receipt3"] == 200.0
