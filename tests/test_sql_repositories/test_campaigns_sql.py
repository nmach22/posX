import sqlite3
import uuid

import pytest

from app.core.classes.errors import DoesntExistError
from app.core.Interfaces.campaign_interface import BuyNGetN, Campaign, Combo, Discount
from app.core.Interfaces.product_interface import Product
from app.infra.sql_repositories.campaign_sql_repository import CampaignSQLRepository
from app.infra.sql_repositories.product_sql_repository import ProductSQLRepository


@pytest.fixture
def connection() -> sqlite3.Connection:
    """Creates a fresh in-memory SQLite connection for each test."""
    return sqlite3.connect(":memory:", check_same_thread=False)


@pytest.fixture
def products_repo(connection: sqlite3.Connection) -> ProductSQLRepository:
    """Creates a ProductSQLRepository for testing campaigns."""
    return ProductSQLRepository(connection)


@pytest.fixture
def campaigns_repo(
    connection: sqlite3.Connection, products_repo: ProductSQLRepository
) -> CampaignSQLRepository:
    """Creates a CampaignSQLRepository with product repository."""
    return CampaignSQLRepository(connection, products_repo)


@pytest.fixture
def sample_product(products_repo: ProductSQLRepository) -> Product:
    """Adds a sample product to the repository."""
    product = Product(id="p1", name="Apple", barcode="12345", price=100)
    products_repo.create(product)
    return product


def test_add_discount_campaign(
    campaigns_repo: CampaignSQLRepository, sample_product: Product
) -> None:
    """Tests adding a discount campaign and retrieving it."""
    campaign = Campaign(
        campaign_id=str(uuid.uuid4()),
        type="discount",
        data=Discount(product_id=sample_product.id, discount_percentage=10),
    )

    campaigns_repo.create(campaign)

    campaigns = campaigns_repo.read_all()
    assert len(campaigns) == 1
    if isinstance(campaigns[0].data, Discount):
        assert campaigns[0].campaign_id == campaign.campaign_id
        assert campaigns[0].data.product_id == sample_product.id
        assert campaigns[0].data.discount_percentage == 10


def test_add_combo_campaign(
    campaigns_repo: CampaignSQLRepository, products_repo: ProductSQLRepository
) -> None:
    """Tests adding a combo campaign with multiple products."""
    product1 = Product(id="p1", name="Apple", barcode="12345", price=100)
    product2 = Product(id="p2", name="Banana", barcode="67890", price=50)
    products_repo.create(product1)
    products_repo.create(product2)

    campaign = Campaign(
        campaign_id=str(uuid.uuid4()),
        type="combo",
        data=Combo(products=["p1", "p2"], discount_percentage=20),
    )

    campaigns_repo.create(campaign)

    campaigns = campaigns_repo.read_all()
    assert len(campaigns) == 1
    if isinstance(campaigns[0].data, Combo):
        assert set(campaigns[0].data.products) == {"p1", "p2"}
        assert campaigns[0].data.discount_percentage == 20


def test_add_buy_n_get_n_campaign(
    campaigns_repo: CampaignSQLRepository, sample_product: Product
) -> None:
    """Tests adding a Buy N Get N campaign."""
    campaign = Campaign(
        campaign_id=str(uuid.uuid4()),
        type="buy n get n",
        data=BuyNGetN(product_id=sample_product.id, buy_quantity=2, get_quantity=1),
    )

    campaigns_repo.create(campaign)

    campaigns = campaigns_repo.read_all()
    assert len(campaigns) == 1
    if isinstance(campaigns[0].data, BuyNGetN):
        assert campaigns[0].data.product_id == sample_product.id
        assert campaigns[0].data.buy_quantity == 2
        assert campaigns[0].data.get_quantity == 1


def test_delete_existing_campaign(
    campaigns_repo: CampaignSQLRepository, sample_product: Product
) -> None:
    """Tests deleting a campaign."""
    campaign = Campaign(
        campaign_id=str(uuid.uuid4()),
        type="discount",
        data=Discount(product_id=sample_product.id, discount_percentage=10),
    )

    campaigns_repo.create(campaign)
    campaigns_repo.delete(campaign.campaign_id)

    campaigns = campaigns_repo.read_all()
    assert len(campaigns) == 0


def test_delete_non_existent_campaign(campaigns_repo: CampaignSQLRepository) -> None:
    """Tests that deleting a non-existent campaign raises DoesntExistError."""
    with pytest.raises(DoesntExistError):
        campaigns_repo.delete(str(uuid.uuid4()))
