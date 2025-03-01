import sqlite3

from app.core.Interfaces.product_interface import Product
from app.core.Interfaces.repository import Repository
from app.infra.in_memory_repositories.product_in_memory_repository import (
    DoesntExistError,
    ExistsError,
)


class ProductSQLRepository(Repository[Product]):
    def __init__(self, connection: sqlite3.Connection):
        self.conn = connection
        self._initialize_db()

    def _initialize_db(self):
        cursor = self.conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS products (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                barcode TEXT UNIQUE NOT NULL,
                price INTEGER NOT NULL
            )
            """
        )
        self.conn.commit()

    def create(self, product: Product) -> None:
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO products (id, name, barcode, price) VALUES (?, ?, ?, ?)",
                (product.id, product.name, product.barcode, product.price),
            )
            self.conn.commit()
        except sqlite3.IntegrityError:
            raise ExistsError

    def read(self, product_id: str) -> Product:
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT id, name, barcode, price FROM products WHERE id = ?",
            (product_id,),
        )
        row = cursor.fetchone()
        if row:
            return Product(id=row[0], name=row[1], barcode=row[2], price=row[3])
        raise DoesntExistError

    def update(self, product: Product) -> None:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            UPDATE products SET price = ? WHERE id = ?
            """,
            (product.price, product.id),
        )
        if cursor.rowcount == 0:
            raise DoesntExistError
        self.conn.commit()

    def delete(self, product_id: str) -> None:
        raise NotImplemented

    def read_all(self) -> list[Product]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, name, barcode, price FROM products")
        rows = cursor.fetchall()
        return [
            Product(id=row[0], name=row[1], barcode=row[2], price=row[3])
            for row in rows
        ]
