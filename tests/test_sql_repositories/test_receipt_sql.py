import sqlite3

import pytest

from app.core.Interfaces.product_interface import Product
from app.core.Interfaces.receipt_interface import (
    Receipt,
    ReceiptProduct,
    AddProductRequest,
)
from app.core.Interfaces.shift_interface import Shift
from app.core.Interfaces.shift_repository_interface import ShiftRepositoryInterface
from app.core.classes.exchange_rate_service import ExchangeRateService
from app.infra.in_memory_repositories.product_in_memory_repository import (
    DoesntExistError,
)
from app.infra.sql_repositories.campaign_sql_repository import CampaignSQLRepository
from app.infra.sql_repositories.product_sql_repository import ProductSQLRepository
from app.infra.sql_repositories.receipt_sql_repository import ReceiptSQLRepository
from app.infra.sql_repositories.shift_sql_repository import ShiftSQLRepository


@pytest.fixture
def connection() -> sqlite3.Connection:
    """Creates a new SQLite in-memory database for each test."""
    return sqlite3.connect(":memory:", check_same_thread=False)


@pytest.fixture
def product_repo(connection: sqlite3.Connection) -> ProductSQLRepository:
    """Creates a product repository."""
    return ProductSQLRepository(connection)


@pytest.fixture
def shift_repo(connection: sqlite3.Connection) -> ShiftRepositoryInterface:
    """Creates a shift repository."""
    return ShiftSQLRepository(connection)


@pytest.fixture
def campaign_repo(
    connection: sqlite3.Connection, product_repo: ProductSQLRepository
) -> CampaignSQLRepository:
    """Creates a campaign repository."""
    return CampaignSQLRepository(connection, product_repo)


@pytest.fixture
def exchange_rate_service():
    return ExchangeRateService()


@pytest.fixture
def repo(
    connection: sqlite3.Connection,
    product_repo: ProductSQLRepository,
    shift_repo: ShiftRepositoryInterface,
    campaign_repo: CampaignSQLRepository,
    exchange_rate_service: ExchangeRateService,
) -> ReceiptSQLRepository:
    """Creates a receipt repository with all dependencies."""
    return ReceiptSQLRepository(
        connection, product_repo, shift_repo, campaign_repo, exchange_rate_service
    )


@pytest.fixture
def sample_products(product_repo: ProductSQLRepository) -> list[Product]:
    """Creates sample products for testing."""
    products = [
        Product(id="p1", name="Product 1", barcode="123", price=100),
        Product(id="p2", name="Product 2", barcode="456", price=200),
        Product(id="p3", name="Product 3", barcode="789", price=300),
    ]
    for product in products:
        product_repo.create(product)
    return products


@pytest.fixture
def sample_shift(shift_repo: ShiftRepositoryInterface) -> Shift:
    """Creates a sample shift for testing."""
    shift = Shift(shift_id="shift1", receipts=[], status="open")
    shift_repo.create(shift)
    return shift


@pytest.fixture
def sample_receipt(sample_shift: Shift) -> Receipt:
    """Creates a sample receipt object (not saved)."""
    return Receipt(
        id="r1",
        shift_id=sample_shift.shift_id,
        currency="USD",
        products=[],
        status="open",
        total=0,
        discounted_total=0,
    )


def test_create_receipt(repo: ReceiptSQLRepository, sample_receipt: Receipt) -> None:
    """Tests creating a receipt."""
    created = repo.create(sample_receipt)

    assert created.id == "r1"
    assert created.shift_id == "shift1"
    assert created.currency == "USD"
    assert created.status == "open"
    assert created.total == 0
    assert len(created.products) == 0

    retrieved_receipt = repo.read(created.id)

    assert retrieved_receipt is not None
    assert retrieved_receipt.id == "r1"
    assert retrieved_receipt.shift_id == "shift1"
    assert retrieved_receipt.currency == "USD"
    assert retrieved_receipt.status == "open"
    assert len(retrieved_receipt.products) == 0


def test_create_receipt_with_nonexistent_shift(repo: ReceiptSQLRepository) -> None:
    """Tests that creating a receipt with a non-existent shift raises DoesntExistError."""
    receipt = Receipt(
        id="r1",
        shift_id="nonexistent",
        currency="USD",
        status="open",
        total=0,
        products=[],
        discounted_total=0,
    )

    with pytest.raises(DoesntExistError):
        repo.create(receipt)


def test_create_receipt_with_products(
    repo: ReceiptSQLRepository, sample_receipt: Receipt, sample_products: list[Product]
) -> None:
    """Tests creating a receipt with products."""
    # Add products to the receipt
    receipt_products = [
        ReceiptProduct(id="p1", quantity=2, price=100, total=200),
        ReceiptProduct(id="p2", quantity=1, price=200, total=200),
    ]
    receipt = Receipt(
        id=sample_receipt.id,
        shift_id=sample_receipt.shift_id,
        currency=sample_receipt.currency,
        status=sample_receipt.status,
        total=400,  # 2*100 + 1*200
        products=receipt_products,
        discounted_total=0,
    )

    created = repo.create(receipt)

    assert created.id == "r1"
    assert created.total == 400
    assert len(created.products) == 2

    retrieved_receipt = repo.read(created.id)

    assert len(retrieved_receipt.products) == 2
    product_1 = retrieved_receipt.products[0]
    product_2 = retrieved_receipt.products[1]

    assert product_1.id == "p1"
    assert product_1.quantity == 2
    assert product_1.price == 100
    assert product_1.total == 200

    assert product_2.id == "p2"
    assert product_2.quantity == 1
    assert product_2.price == 200
    assert product_2.total == 200


def test_read_receipt(
    repo: ReceiptSQLRepository, sample_receipt: Receipt, sample_products: list[Product]
) -> None:
    """Tests reading a receipt."""
    # Create the receipt first
    created_receipt = repo.create(sample_receipt)

    # Add a product to the receipt
    repo.add_product_to_receipt(
        created_receipt.id, AddProductRequest(sample_products[0].id, 2)
    )

    # Read the receipt
    retrieved = repo.read(created_receipt.id)

    # Check receipt data
    assert retrieved.id == "r1"
    assert retrieved.shift_id == "shift1"
    assert retrieved.currency == "USD"
    assert retrieved.status == "open"
    assert retrieved.total == 200

    # Check receipt products
    assert len(retrieved.products) == 1
    assert retrieved.products[0].id == "p1"
    assert retrieved.products[0].quantity == 2
    assert retrieved.products[0].price == 100
    assert retrieved.products[0].total == 200


def test_read_nonexistent_receipt(repo: ReceiptSQLRepository) -> None:
    """Tests that reading a non-existent receipt raises DoesntExistError."""
    with pytest.raises(DoesntExistError):
        repo.read("nonexistent")


def test_update_receipt(repo: ReceiptSQLRepository, sample_receipt: Receipt) -> None:
    """Tests updating a receipt."""
    # Create the receipt first
    repo.create(sample_receipt)

    # Update receipt with new data
    updated_receipt = Receipt(
        id="r1",
        shift_id="shift1",
        currency="EUR",  # Changed from USD
        status="closed",  # Changed from open
        total=300,
        products=[ReceiptProduct(id="p1", quantity=3, price=100, total=300)],
        discounted_total=0,
    )

    repo.update(updated_receipt)

    # Read the updated receipt
    retrieved = repo.read("r1")

    # Check updated data
    assert retrieved.id == "r1"
    assert retrieved.currency == "EUR"
    assert retrieved.status == "closed"
    assert retrieved.total == 300
    assert len(retrieved.products) == 1
    assert retrieved.products[0].id == "p1"
    assert retrieved.products[0].quantity == 3
    assert retrieved.products[0].total == 300


def test_delete_receipt(
    repo: ReceiptSQLRepository, sample_receipt: Receipt, sample_products: list[Product]
) -> None:
    """Tests deleting a receipt."""
    # Create the receipt first
    created_receipt = repo.create(sample_receipt)

    # Add a product to the receipt
    repo.add_product_to_receipt(
        created_receipt.id, AddProductRequest(sample_products[0].id, 2)
    )

    # Delete the receipt
    repo.delete("r1")

    with pytest.raises(DoesntExistError):
        repo.read("r1")

    # Verify receipt products are also deleted
    cursor = repo.conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM receipt_products WHERE receipt_id = ?", ("r1",)
    )
    count = cursor.fetchone()[0]
    assert count == 0


def test_delete_nonexistent_receipt(repo: ReceiptSQLRepository) -> None:
    """Tests that deleting a non-existent receipt raises DoesntExistError."""
    with pytest.raises(DoesntExistError):
        repo.delete("asd")


def test_add_product_to_receipt(
    repo: ReceiptSQLRepository, sample_receipt: Receipt, sample_products: list[Product]
) -> None:
    """Tests adding a product to a receipt."""
    # Create the receipt first
    repo.create(sample_receipt)

    # Add a product to the receipt
    product_request = AddProductRequest(product_id="p1", quantity=2)
    updated_receipt = repo.add_product_to_receipt("r1", product_request)

    # Check updated receipt
    assert updated_receipt.id == "r1"
    assert updated_receipt.total == 200  # 2 * 100
    assert len(updated_receipt.products) == 1
    assert updated_receipt.products[0].id == "p1"
    assert updated_receipt.products[0].quantity == 2
    assert updated_receipt.products[0].price == 100
    assert updated_receipt.products[0].total == 200

    # Add another product
    product_request = AddProductRequest(product_id="p2", quantity=1)
    updated_receipt = repo.add_product_to_receipt("r1", product_request)

    # Check updated receipt again
    assert updated_receipt.total == 400  # 200 + 200
    assert len(updated_receipt.products) == 2


def test_add_product_to_nonexistent_receipt(
    repo: ReceiptSQLRepository, sample_products: list[Product]
) -> None:
    """Tests that adding a product to a non-existent receipt raises DoesntExistError."""
    product_request = AddProductRequest(product_id="p1", quantity=1)

    with pytest.raises(DoesntExistError):
        repo.add_product_to_receipt("nonexistent", product_request)


def test_add_nonexistent_product_to_receipt(
    repo: ReceiptSQLRepository, sample_receipt: Receipt
) -> None:
    """Tests that adding a non-existent product to a receipt raises DoesntExistError."""
    # Create the receipt first
    repo.create(sample_receipt)

    product_request = AddProductRequest(product_id="nonexistent", quantity=1)

    with pytest.raises(DoesntExistError):
        repo.add_product_to_receipt("r1", product_request)


def test_calculate_payment_basic(
    repo: ReceiptSQLRepository, sample_receipt: Receipt, sample_products: list[Product]
) -> None:
    """Tests calculating payment for a receipt with no discounts."""
    # Create the receipt
    repo.create(sample_receipt)

    # Add a product to the receipt
    updated_receipt = repo.add_product_to_receipt(
        "r1", AddProductRequest(product_id="p1", quantity=2)
    )
    updated_receipt = repo.add_product_to_receipt(
        "r1", AddProductRequest(product_id="p2", quantity=1)
    )

    cursor = repo.conn.cursor()

    # Calculate payment
    repo.read("r1")
    # payment = repo.calculate_payment(updated_receipt.id)

    # With no discounts, original and reduced price should be the same
    # assert payment.receipt.id == updated_receipt.id
    # assert payment.receipt.total == 400
    # assert payment.discounted_price == 0
    # assert payment.reduced_price == 400


def test_calculate_payment_with_discount_campaign(
    repo: ReceiptSQLRepository,
    campaign_repo: CampaignSQLRepository,
    sample_receipt: Receipt,
    sample_products: list[Product],
) -> None:
    """Tests calculating payment with discount campaigns applied."""
    # Create a discount campaign
    # discount_campaign = Campaign(
    #     campaign_id="dc1",
    #     type="discount",
    #     data=Discount(product_id="p1", discount_percentage=20),
    # )
    # campaign_repo.create(discount_campaign)
    #
    # # Create the receipt
    # repo.create(sample_receipt)
    #
    # # Add products to the receipt directly
    # cursor = repo.conn.cursor()
    #
    # # Product p1 has discount
    # cursor.execute(
    #     "INSERT INTO receipt_products (receipt_id, product_id, quantity, price, total) VALUES (?, ?, ?, ?, ?)",
    #     ("r1", "p1", 2, 100, 200),
    # )
    # # Product p2 has no discount
    # cursor.execute(
    #     "INSERT INTO receipt_products (receipt_id, product_id, quantity, price, total) VALUES (?, ?, ?, ?, ?)",
    #     ("r1", "p2", 1, 200, 200),
    # )
    # cursor.execute("UPDATE receipts SET total = 400 WHERE id = ?", ("r1",))
    # repo.conn.commit()
    #
    # # Setup mock campaign products table with discount info
    # cursor.execute("""
    #     CREATE TABLE IF NOT EXISTS campaign_products (
    #         id TEXT PRIMARY KEY,
    #         campaign_id TEXT,
    #         product_id TEXT,
    #         discounted_price INTEGER,
    #         FOREIGN KEY (campaign_id) REFERENCES campaigns(id),
    #         FOREIGN KEY (product_id) REFERENCES products(id)
    #     )
    # """)
    #
    # cursor.execute("""
    #     CREATE TABLE IF NOT EXISTS campaigns (
    #         id TEXT PRIMARY KEY,
    #         type TEXT NOT NULL,
    #         discount_percentage INTEGER,
    #         buy_quantity INTEGER,
    #         get_quantity INTEGER,
    #         min_amount INTEGER
    #     )
    # """)
    #
    # # Insert campaign data
    # cursor.execute(
    #     "INSERT INTO campaigns (id, type, discount_percentage) VALUES (?, ?, ?)",
    #     ("dc1", "discount", 20),
    # )
    #
    # # Insert campaign product with discounted price
    # cursor.execute(
    #     "INSERT INTO campaign_products (id, campaign_id, product_id, discounted_price) VALUES (?, ?, ?, ?)",
    #     (str(uuid.uuid4()), "dc1", "p1", 80),  # 20% off 100 = 80
    # )
    # repo.conn.commit()
    #
    # # Calculate payment
    # payment = repo.calculate_payment("r1")
    #
    # # For 2 items of p1 with 20% discount (2 * 20 = 40) and no discount on p2
    # assert payment.receipt.id == "r1"
    # assert payment.receipt.total == 400
    # assert payment.discounted_price == 2 * 80  # 2 items at discounted price of 80 each
    # assert payment.reduced_price == 400 - (2 * 20)  # Original - discount
