import sqlite3
from dataclasses import dataclass

from app.core.Interfaces.product_repository_interface import ProductRepositoryInterface
from app.core.Interfaces.receipt_interface import Receipt
from app.core.Interfaces.shift_interface import Shift, Report, SalesReport
from app.core.Interfaces.shift_repository_interface import ShiftRepositoryInterface
from app.infra.in_memory_repositories.product_in_memory_repository import (
    DoesntExistError,
)


@dataclass
class ShiftSQLRepository(ShiftRepositoryInterface):
    def __init__(
        self,
        connection: sqlite3.Connection,
        products_repo: ProductRepositoryInterface,
    ):
        self.conn = connection
        self.products = products_repo

        self._initialize_database()

    def _initialize_database(self):
        """Create necessary tables if they don't exist."""

        cursor = self.conn.cursor()
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS shifts (
                shift_id TEXT PRIMARY KEY,
                status TEXT NOT NULL
            );
        """)
        self.conn.commit()

    def add_shift(self, shift: Shift) -> None:
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO shifts (shift_id, status) VALUES (?, ?)",
            (shift.shift_id, shift.status),
        )
        self.conn.commit()

    def close_shift(self, shift_id: str) -> None:
        """Mark shift as closed."""

        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE shifts SET status = 'closed' WHERE shift_id = ?", (shift_id,)
        )
        if cursor.rowcount == 0:
            raise DoesntExistError(f"Shift with ID {shift_id} not found.")
        self.conn.commit()

    def add_receipt_to_shift(self, receipt: Receipt) -> None:
        """Add a receipt to a shift in the database."""
        # with sqlite3.connect(self.db_path) as conn:
        #     cursor = self.conn.cursor()
        #     cursor.execute(
        #         "INSERT INTO receipts (receipt_id, shift_id, total, status) VALUES (?, ?, ?, ?)",
        #         (receipt.receipt_id, receipt.shift_id, receipt.total, receipt.status)
        #     )
        #     for product in receipt.products:
        #         cursor.execute(
        #             "INSERT INTO products (product_id, receipt_id, quantity, total_price) VALUES (?, ?, ?, ?)",
        #             (product.id, receipt.receipt_id, product.quantity, product.total)
        #         )
        #     self.conn.commit()

    def get_x_report(self, shift_id: str) -> Report:
        cursor = self.conn.cursor()

        cursor.execute("SELECT status FROM shifts WHERE shift_id = ?", (shift_id,))
        result = cursor.fetchone()
        if not result:
            raise DoesntExistError(f"Shift with ID {shift_id} not found.")
        if result[0] != "open":
            raise ValueError(f"Cannot generate X Report for closed shift {shift_id}.")

        # Get receipts for the shift that are closed
        cursor.execute(
            "SELECT r.id, r.total "
            "FROM receipts r "
            "WHERE r.shift_id = ? AND r.status = 'closed'",
            (shift_id,),
        )
        receipts = cursor.fetchall()
        n_receipts = len(receipts)
        revenue = sum(total for _, total in receipts)

        product_summary = {}
        cursor.execute(
            """
            SELECT rp.product_id, SUM(rp.quantity) AS total_quantity, SUM(rp.total) AS total_price
            FROM receipt_products rp
            JOIN receipts r ON rp.receipt_id = r.id
            WHERE r.shift_id = ? AND r.status = 'closed'
            GROUP BY rp.product_id
            """,
            (shift_id,),
        )
        for product_id, total_quantity, total_price in cursor.fetchall():
            product_summary[product_id] = {
                "quantity": total_quantity,
                "total_price": total_price,
            }

        products = [
            {
                "id": pid,
                "quantity": data["quantity"],
                "total_price": data["total_price"],
            }
            for pid, data in product_summary.items()
        ]

        return Report(
            shift_id=shift_id,
            n_receipts=n_receipts,
            revenue=revenue,
            products=products,
        )

    def get_z_report(self, shift_id: str) -> Report:
        """Generate a Z report for a shift and close it."""
        report = self.get_x_report(shift_id)
        self.close_shift(shift_id)
        return Report(
            shift_id=shift_id,
            n_receipts=report.n_receipts,
            revenue=report.revenue,
            products=report.products,
        )

    def get_lifetime_sales_report(self) -> SalesReport:
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT COUNT(*), SUM(total) FROM receipts WHERE status = 'closed'"
        )
        total_receipts, total_revenue = cursor.fetchone()

        product_summary = {}
        cursor.execute(
            """
            SELECT product_id, SUM(quantity), SUM(total_price)
            FROM products
            WHERE receipt_id IN (SELECT receipt_id FROM receipts WHERE status = 'closed')
            GROUP BY product_id
            """
        )
        for product_id, quantity, total_price in cursor.fetchall():
            product_summary[product_id] = {
                "quantity": quantity,
                "total_price": total_price,
            }

        products = [
            {
                "id": pid,
                "quantity": data["quantity"],
                "total_price": data["total_price"],
            }
            for pid, data in product_summary.items()
        ]

        return SalesReport(
            total_receipts=total_receipts or 0,
            total_revenue=total_revenue or 0.0,
            products=products,
        )
