import sqlite3
from unittest.mock import MagicMock

import pytest

from app.core.classes.errors import AlreadyClosedError, DoesntExistError
from app.core.classes.exchange_rate_service import ExchangeRateService
from app.core.Interfaces.campaign_interface import (
    BuyNGetN,
    Campaign,
    Combo,
    Discount,
    ReceiptDiscount,
)
from app.core.Interfaces.product_interface import Product
from app.core.Interfaces.receipt_interface import (
    AddProductRequest,
    Receipt,
    ReceiptProduct,
)
from app.core.Interfaces.shift_interface import Shift
from app.core.Interfaces.shift_repository_interface import ShiftRepositoryInterface
from app.infra.sql_repositories.campaign_sql_repository import CampaignSQLRepository
from app.infra.sql_repositories.product_sql_repository import ProductSQLRepository
from app.infra.sql_repositories.receipt_sql_repository import ReceiptSQLRepository
from app.infra.sql_repositories.shift_sql_repository import ShiftSQLRepository
from app.infra.sqlite import Sqlite


@pytest.fixture(scope="function")
def connection() -> sqlite3.Connection:
    """Creates a new SQLite in-memory database for each test."""
    connect = sqlite3.connect(":memory:", check_same_thread=False)
    Sqlite(connect)
    return connect


@pytest.fixture(scope="function")
def product_repo(connection: sqlite3.Connection) -> ProductSQLRepository:
    """Creates a product repository."""
    return ProductSQLRepository(connection)


@pytest.fixture(scope="function")
def shift_repo(connection: sqlite3.Connection) -> ShiftRepositoryInterface:
    """Creates a shift repository."""
    return ShiftSQLRepository(connection)


@pytest.fixture(scope="function")
def campaign_repo(
    connection: sqlite3.Connection, product_repo: ProductSQLRepository
) -> CampaignSQLRepository:
    """Creates a campaign repository."""
    return CampaignSQLRepository(connection, product_repo)


@pytest.fixture(scope="function")
def exchange_rate_service() -> ExchangeRateService:
    """Creates an exchange rate service mock."""
    service = MagicMock(spec=ExchangeRateService)
    service.get_exchange_rate.return_value = 2.5  # 1 GEL = 2.5 USD for testing
    return service


@pytest.fixture(scope="function")
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


@pytest.fixture(scope="function")
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


@pytest.fixture(scope="function")
def sample_shift(shift_repo: ShiftRepositoryInterface) -> Shift:
    """Creates a sample shift for testing."""
    shift = Shift(shift_id="shift1", receipts=[], status="open")
    shift_repo.create(shift)
    return shift


@pytest.fixture(scope="function")
def sample_closed_shift(shift_repo: ShiftRepositoryInterface) -> Shift:
    """Creates a sample closed shift for testing."""
    shift = Shift(shift_id="shift2", receipts=[], status="closed")
    shift_repo.create(shift)
    return shift


@pytest.fixture(scope="function")
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


@pytest.fixture(scope="function")
def sample_receipt_gel(sample_shift: Shift) -> Receipt:
    """Creates a sample receipt object (not saved)."""
    return Receipt(
        id="r1",
        shift_id=sample_shift.shift_id,
        currency="GEL",
        products=[],
        status="open",
        total=0,
        discounted_total=0,
    )


@pytest.fixture(scope="function")
def sample_receipt_with_products(
    sample_shift: Shift, sample_products: list[Product]
) -> Receipt:
    """Creates a sample receipt with products."""
    receipt_products = [
        ReceiptProduct(
            id=sample_products[0].id,
            quantity=2,
            price=int(sample_products[0].price),
            total=200,
        ),
        ReceiptProduct(
            id=sample_products[1].id,
            quantity=1,
            price=int(sample_products[1].price),
            total=200,
        ),
    ]
    return Receipt(
        id="r2",
        shift_id=sample_shift.shift_id,
        currency="USD",
        products=receipt_products,
        status="open",
        total=400,
        discounted_total=400,
    )


@pytest.fixture(scope="function")
def sample_campaigns(
    campaign_repo: CampaignSQLRepository, sample_products: list[Product]
) -> list[Campaign]:
    """Creates sample campaigns for testing."""
    # Discount campaign for Product 1
    discount_campaign = Campaign(
        campaign_id="c1",
        type="discount",
        data=Discount(product_id=sample_products[0].id, discount_percentage=10),
    )

    # Buy 1, Get 1 campaign for Product 2
    buy_n_campaign = Campaign(
        campaign_id="c2",
        type="buy n get n",
        data=BuyNGetN(product_id=sample_products[1].id, buy_quantity=1, get_quantity=1),
    )

    # Combo campaign for Products 1 and 3
    combo_campaign = Campaign(
        campaign_id="c3",
        type="combo",
        data=Combo(products=["p1", "p2"], discount_percentage=15),
    )

    # Receipt discount campaign
    receipt_campaign = Campaign(
        campaign_id="c4",
        type="receipt discount",
        data=ReceiptDiscount(min_amount=100, discount_percentage=10),
    )

    campaigns = [discount_campaign, buy_n_campaign, combo_campaign, receipt_campaign]

    for campaign in campaigns:
        campaign_repo.create(campaign)

    return campaigns


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
    """Tests that creating a receipt with non-existent shift raises DoesntExistError."""
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
    repo: ReceiptSQLRepository, sample_receipt_with_products: Receipt
) -> None:
    """Tests creating a receipt with products."""
    created = repo.create(sample_receipt_with_products)

    assert created.id == "r2"
    assert created.total == 400
    assert len(created.products) == 2

    retrieved = repo.read(created.id)
    assert len(retrieved.products) == 2
    assert retrieved.products[0].id == "p1"
    assert retrieved.products[0].quantity == 2
    assert retrieved.products[0].price == 100
    assert retrieved.products[0].total == 200
    assert retrieved.products[1].id == "p2"
    assert retrieved.products[1].quantity == 1
    assert retrieved.products[1].price == 200
    assert retrieved.products[1].total == 200


def test_create_receipt_closed_shift(
    repo: ReceiptSQLRepository, sample_closed_shift: Shift
) -> None:
    """Tests creating a receipt with a closed shift."""
    receipt = Receipt(
        id="r4",
        shift_id=sample_closed_shift.shift_id,
        currency="USD",
        products=[],
        status="open",
        total=0,
        discounted_total=0,
    )

    with pytest.raises(AlreadyClosedError) as exc:
        repo.create(receipt)

    assert "already closed" in str(exc.value)


def test_read_nonexistent_receipt(repo: ReceiptSQLRepository) -> None:
    """Tests reading a non-existent receipt."""
    with pytest.raises(DoesntExistError) as exc:
        repo.read("nonexistent_receipt")

    assert "does not exist" in str(exc.value)


def test_update_receipt(
    repo: ReceiptSQLRepository, sample_receipt: Receipt, sample_products: list[Product]
) -> None:
    """Tests updating a receipt."""
    # Create initial receipt
    created = repo.create(sample_receipt)

    # Update receipt with new products
    updated_products = [
        ReceiptProduct(id=sample_products[0].id, quantity=3, price=100, total=300)
    ]
    updated_receipt = Receipt(
        id=created.id,
        shift_id=created.shift_id,
        currency="EUR",  # Changed currency
        products=updated_products,
        status="open",
        total=300,
        discounted_total=300,
    )

    repo.update(updated_receipt)

    # Verify update
    retrieved = repo.read(created.id)
    assert retrieved.currency == "EUR"
    assert retrieved.total == 300
    assert len(retrieved.products) == 1
    assert retrieved.products[0].id == sample_products[0].id
    assert retrieved.products[0].quantity == 3


def test_delete_receipt(repo: ReceiptSQLRepository, sample_receipt: Receipt) -> None:
    """Tests deleting a receipt."""
    created = repo.create(sample_receipt)

    repo.delete(created.id)

    with pytest.raises(DoesntExistError):
        repo.read(created.id)


def test_delete_nonexistent_receipt(repo: ReceiptSQLRepository) -> None:
    """Tests deleting a non-existent receipt."""
    with pytest.raises(DoesntExistError) as exc:
        repo.delete("nonexistent_receipt")

    assert "does not exist" in str(exc.value)


def test_add_product_to_receipt(
    repo: ReceiptSQLRepository, sample_receipt: Receipt, sample_products: list[Product]
) -> None:
    """Tests adding a product to a receipt."""
    created = repo.create(sample_receipt)

    product_request = AddProductRequest(product_id=sample_products[0].id, quantity=2)
    updated = repo.add_product_to_receipt(created.id, product_request)

    assert updated.total == 200
    assert len(updated.products) == 1
    assert updated.products[0].id == sample_products[0].id
    assert updated.products[0].quantity == 2
    assert updated.products[0].price == 100
    assert updated.products[0].total == 200


def test_add_product_to_nonexistent_receipt(
    repo: ReceiptSQLRepository, sample_products: list[Product]
) -> None:
    """Tests adding a product to a non-existent receipt."""
    product_request = AddProductRequest(product_id=sample_products[0].id, quantity=1)

    with pytest.raises(DoesntExistError) as exc:
        repo.add_product_to_receipt("nonexistent_receipt", product_request)

    assert "does not exist" in str(exc.value)


def test_add_nonexistent_product_to_receipt(
    repo: ReceiptSQLRepository, sample_receipt: Receipt
) -> None:
    """Tests adding a non-existent product to a receipt."""
    created = repo.create(sample_receipt)

    product_request = AddProductRequest(product_id="nonexistent_product", quantity=1)

    with pytest.raises(DoesntExistError) as exc:
        repo.add_product_to_receipt(created.id, product_request)

    assert "does not exist" in str(exc.value)


def test_calculate_payment_basic(
    repo: ReceiptSQLRepository, sample_receipt: Receipt, sample_products: list[Product]
) -> None:
    """Tests basic payment calculation without discounts."""
    created = repo.create(sample_receipt)

    # Add products to receipt
    repo.add_product_to_receipt(
        created.id, AddProductRequest(product_id=sample_products[0].id, quantity=2)
    )

    payment = repo.calculate_payment(created.id)

    assert payment.receipt.id == created.id
    assert payment.receipt.total == 5.0  # 200 cents converted to USD (200*2.5/100)
    assert payment.discounted_price == 5.0  # No discount
    assert payment.reduced_price == 0.0  # No reduction


def test_calculate_payment_with_discount_campaign(
    repo: ReceiptSQLRepository,
    sample_receipt_gel: Receipt,
    sample_products: list[Product],
    sample_campaigns: list[Campaign],
) -> None:
    """Tests payment calculation with a discount campaign."""
    created = repo.create(sample_receipt_gel)

    # Add product with discount campaign (10% off)
    updated = repo.add_product_to_receipt(
        created.id, AddProductRequest(product_id=sample_products[0].id, quantity=1)
    )

    assert updated.products[0].quantity == 1
    payment = repo.calculate_payment(created.id)
    # Expect 10% discount on 100 whites = 90 whites = 0.9 GEL
    assert payment.receipt.total == 1.0
    assert payment.discounted_price == 0.9
    assert payment.reduced_price == 0.1

    # add another product
    updated = repo.add_product_to_receipt(
        created.id, AddProductRequest(product_id=sample_products[1].id, quantity=2)
    )
    assert updated.products[1].quantity == 2
    payment = repo.calculate_payment(created.id)

    assert payment.receipt.total == 5.0
    assert payment.discounted_price == 2.57
    assert payment.reduced_price == 5 - 2.57


def test_calculate_payment_with_buy_n_get_n_campaign(
    repo: ReceiptSQLRepository,
    sample_receipt_gel: Receipt,
    sample_products: list[Product],
    sample_campaigns: list[Campaign],
) -> None:
    """Tests payment calculation with a buy N get N campaign."""
    created = repo.create(sample_receipt_gel)

    # Add product with Buy 1, Get 1 campaign
    repo.add_product_to_receipt(
        created.id, AddProductRequest(product_id=sample_products[1].id, quantity=2)
    )

    payment = repo.calculate_payment(created.id)

    assert payment.receipt.total == 4.0
    assert payment.discounted_price == 1.8
    assert payment.reduced_price == 4.0 - 1.8


def test_calculate_payment_with_combo_campaign(
    repo: ReceiptSQLRepository,
    sample_receipt: Receipt,
    sample_products: list[Product],
    sample_campaigns: list[Campaign],
) -> None:
    """Tests payment calculation with a combo campaign."""
    created = repo.create(sample_receipt)

    # Add both products in the combo (Products 1 and 3)
    repo.add_product_to_receipt(
        created.id, AddProductRequest(product_id=sample_products[0].id, quantity=1)
    )
    repo.add_product_to_receipt(
        created.id, AddProductRequest(product_id=sample_products[2].id, quantity=1)
    )

    payment = repo.calculate_payment(created.id)

    assert payment.receipt.total == 10.0
    assert payment.discounted_price == 8.77
    assert payment.reduced_price == 1.22


def test_add_payment(
    repo: ReceiptSQLRepository,
    sample_receipt: Receipt,
    sample_products: list[Product],
    sample_campaigns: list[Campaign],
) -> None:
    """Tests adding payment to a receipt."""
    created = repo.create(sample_receipt)

    # Add product with discount campaign
    repo.add_product_to_receipt(
        created.id, AddProductRequest(product_id=sample_products[0].id, quantity=2)
    )

    payment = repo.add_payment(created.id)

    # Verify payment calculation
    assert payment.receipt.id == created.id
    assert payment.discounted_price == 4.05  # With 10% discount

    # Verify receipt was updated with discounted total
    updated = repo.read(created.id)
    assert updated.discounted_total == 4.05


def test_add_payment_nonexistent_receipt(repo: ReceiptSQLRepository) -> None:
    """Tests adding payment to a non-existent receipt."""
    with pytest.raises(DoesntExistError) as exc:
        repo.add_payment("nonexistent_receipt")

    assert "does not exist" in str(exc.value)


def test_exchange_rate_conversion(
    repo: ReceiptSQLRepository,
    sample_receipt: Receipt,
    sample_products: list[Product],
    exchange_rate_service: ExchangeRateService,
) -> None:
    """Tests currency conversion in payment calculation."""
    created = repo.create(sample_receipt)

    # Add product
    repo.add_product_to_receipt(
        created.id, AddProductRequest(product_id=sample_products[0].id, quantity=1)
    )

    payment = repo.calculate_payment(created.id)

    assert payment.receipt.total == 2.5
    assert payment.discounted_price == 2.5
    assert payment.receipt.currency == "USD"


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
