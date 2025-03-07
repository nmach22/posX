import sqlite3

import pytest

from app.core.classes.errors import DoesntExistError
from app.core.Interfaces.shift_interface import Shift
from app.infra.sql_repositories.shift_sql_repository import ShiftSQLRepository


@pytest.fixture
def repo() -> ShiftSQLRepository:
    """Creates a new SQLite in-memory database for each test."""
    connection = sqlite3.connect(":memory:", check_same_thread=False)

    # Create additional test tables needed for reports
    cursor = connection.cursor()
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS receipts (
            id TEXT PRIMARY KEY,
            shift_id TEXT NOT NULL,
            currency TEXT NOT NULL,
            status TEXT NOT NULL,
            total INTEGER NOT NULL,
            discounted_total INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS receipt_products (
            receipt_id TEXT,
            product_id TEXT,
            quantity INTEGER,
            price INTEGER,
            total INTEGER
        );
    """)
    connection.commit()

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
    shift = Shift(shift_id="shift1", receipts=[], status="open")

    repo.create(shift)
    updated_shift = Shift(shift_id="shift1", receipts=[], status="closed")
    repo.update(updated_shift)

    retrieved = repo.read("shift1")
    assert retrieved.status == "closed"


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

    shift = Shift(shift_id="shift1", receipts=[], status="open")
    repo.create(shift)

    # Add test data: receipts and products
    cursor = repo.conn.cursor()

    # Add receipts
    cursor.executescript("""
        INSERT INTO receipts (id,shift_id,currency,status,total,discounted_total)
        VALUES
            ('receipt1', 'shift1',  'USD', 'closed', 100, 100),
            ('receipt2', 'shift1',  'USD', 'closed', 150, 150),
            ('receipt3', 'shift1',  'EUR', 'closed', 200, 200);

        INSERT INTO receipt_products (receipt_id, product_id, quantity)
        VALUES
            ('receipt1', 'product1', 2),
            ('receipt1', 'product2', 1),
            ('receipt2', 'product1', 3),
            ('receipt3', 'product3', 4);
    """)
    repo.conn.commit()

    # Get X report
    report = repo.get_x_report("shift1")

    # Verify report contents
    assert report.shift_id == "shift1"
    assert report.n_receipts == 3
    assert report.revenue == {"USD": 250, "EUR": 200}

    # Verify products data - exact order might be different so check contents
    product_ids = {p["id"] for p in report.products}
    assert product_ids == {"product1", "product2", "product3"}

    # Find each product and check quantity
    for product in report.products:
        if product["id"] == "product1":
            assert product["quantity"] == 5
        elif product["id"] == "product2":
            assert product["quantity"] == 1
        elif product["id"] == "product3":
            assert product["quantity"] == 4


def test_get_x_report_for_nonexistent_shift(repo: ShiftSQLRepository) -> None:
    """Tests that getting X report for a non-existent shift raises DoesntExistError."""
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
    shift1 = Shift(shift_id="shift1", receipts=[], status="open")
    shift2 = Shift(shift_id="shift2", receipts=[], status="closed")
    repo.create(shift1)
    repo.create(shift2)

    cursor = repo.conn.cursor()
    cursor.executescript("""
        INSERT INTO receipts (id,shift_id,currency,status,total,discounted_total)
        VALUES
            ('receipt1', 'shift1',  'USD', 'closed', 100, 100),
            ('receipt2', 'shift1',  'USD', 'closed', 150, 150),
            ('receipt3', 'shift2',  'EUR', 'closed', 200, 200),
            ('receipt4', 'shift2',  'USD', 'open', 75, 75);

    """)
    repo.conn.commit()

    report = repo.get_lifetime_sales_report()

    # Verify report contents - should only count closed receipts
    assert report.total_receipts == 3  # Excludes the open receipt
    assert report.total_revenue == {"USD": 250.0, "EUR": 200.0}

    # Verify closed receipts
    receipt_ids = {r.receipt_id for r in report.closed_receipts}
    assert receipt_ids == {"receipt1", "receipt2", "receipt3"}

    # Find each receipt and check payment
    payment_map = {r.receipt_id: r.calculated_payment for r in report.closed_receipts}
    assert payment_map["receipt1"] == 100
    assert payment_map["receipt2"] == 150
    assert payment_map["receipt3"] == 200
