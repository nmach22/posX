import sqlite3

import pytest

from app.core.Interfaces.product_interface import Product
from app.infra.in_memory_repositories.product_in_memory_repository import (
    DoesntExistError,
    ExistsError,
)
from app.infra.sql_repositories.product_sql_repository import ProductSQLRepository


@pytest.fixture
def repo() -> ProductSQLRepository:
    """Creates a new SQLite in-memory database for each test."""
    connection = sqlite3.connect(":memory:", check_same_thread=False)
    return ProductSQLRepository(connection)


def test_add_and_get_product(repo: ProductSQLRepository) -> None:
    """Tests adding a product and retrieving it."""
    product = Product(id="1", name="Apple", barcode="12345", price=100)

    repo.create(product)
    retrieved = repo.read("1")

    assert retrieved.id == "1"
    assert retrieved.name == "Apple"
    assert retrieved.barcode == "12345"
    assert retrieved.price == 100


def test_add_duplicate_product(repo: ProductSQLRepository) -> None:
    """Tests that adding a duplicate product raises ExistsError."""
    product = Product(id="1", name="Apple", barcode="12345", price=100)

    repo.create(product)

    with pytest.raises(ExistsError):
        repo.create(product)


def test_get_non_existent_product(repo: ProductSQLRepository) -> None:
    """Tests that retrieving a non-existent product raises DoesntExistError."""
    with pytest.raises(DoesntExistError):
        repo.read("999")


def test_update_product(repo: ProductSQLRepository) -> None:
    """Tests updating a product's price."""
    product = Product(id="1", name="Apple", barcode="12345", price=100)

    repo.create(product)
    updated_product = Product(id="1", name="Apple", barcode="12345", price=200)
    repo.update(updated_product)

    retrieved = repo.read("1")
    assert retrieved.price == 200


def test_update_non_existent_product(repo: ProductSQLRepository) -> None:
    """Tests that updating a non-existent product raises DoesntExistError."""
    product = Product(id="999", name="Orange", barcode="67890", price=150)

    with pytest.raises(DoesntExistError):
        repo.update(product)


def test_read_all_products(repo: ProductSQLRepository) -> None:
    """Tests retrieving all products."""
    product1 = Product(id="1", name="Apple", barcode="12345", price=100)
    product2 = Product(id="2", name="Banana", barcode="67890", price=50)

    repo.create(product1)
    repo.create(product2)

    products = repo.read_all()
    assert len(products) == 2
    assert {p.id for p in products} == {"1", "2"}
