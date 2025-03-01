import sqlite3
from dataclasses import dataclass
from typing import Dict

from app.core.Interfaces.product_interface import Product
from app.core.Interfaces.receipt_interface import Receipt
from app.core.Interfaces.repository import Repository
from app.core.Interfaces.shift_interface import (
    ClosedReceipt,
    Report,
    SalesReport,
    Shift,
)
from app.core.Interfaces.shift_repository_interface import ShiftRepositoryInterface
from app.infra.in_memory_repositories.product_in_memory_repository import (
    DoesntExistError,
)


@dataclass
class ShiftSQLRepository(ShiftRepositoryInterface):
    def __init__(
        self,
        connection: sqlite3.Connection,
        products_repo: Repository[Product],
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
        cursor = self.conn.cursor()
        cursor.execute("SELECT status FROM shifts WHERE shift_id = ?", (shift_id,))
        row = cursor.fetchone()
        if row is None:
            raise DoesntExistError(f"Shift with ID {shift_id} not found.")
        current_status = row[0]
        if current_status == "closed":
            raise ValueError(f"Shift with ID {shift_id} is already closed.")
        cursor.execute(
            "UPDATE shifts SET status = 'closed' WHERE shift_id = ?", (shift_id,)
        )
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

    # def get_x_report(self, shift_id: str) -> Report:
    #     cursor = self.conn.cursor()
    #
    #     cursor.execute("SELECT status FROM shifts WHERE shift_id = ?", (shift_id,))
    #     result = cursor.fetchone()
    #     if not result:
    #         raise DoesntExistError(f"Shift with ID {shift_id} not found.")
    #     if result[0] != "open":
    #         raise ValueError(f"Cannot generate X Report for closed shift {shift_id}.")
    #
    #     cursor.execute(
    #         "SELECT r.id, r.total "
    #         "FROM receipts r "
    #         "WHERE r.shift_id = ? AND r.status = 'closed'",
    #         (shift_id,),
    #     )
    #     receipts = cursor.fetchall()
    #     n_receipts = len(receipts)
    #     revenue = sum(total for _, total in receipts)
    #
    #     product_summary = {}
    #     cursor.execute(
    #         """
    #         SELECT rp.product_id, SUM(rp.quantity) AS total_quantity
    #         FROM receipt_products rp
    #         JOIN receipts r ON rp.receipt_id = r.id
    #         WHERE r.shift_id = ? AND r.status = 'closed'
    #         GROUP BY rp.product_id
    #         """,
    #         (shift_id,),
    #     )
    #     for product_id, total_quantity in cursor.fetchall():
    #         product_summary[product_id] = {
    #             "quantity": total_quantity
    #         }
    #
    #     products = [
    #         {
    #             "id": pid,
    #             "quantity": data["quantity"]
    #         }
    #         for pid, data in product_summary.items()
    #     ]
    #
    #     return Report(
    #         shift_id=shift_id,
    #         n_receipts=n_receipts,
    #         revenue=revenue,
    #         products=products,
    #     )

    def get_x_report(self, shift_id: str) -> Report:
        cursor = self.conn.cursor()

        cursor.execute("SELECT status FROM shifts WHERE shift_id = ?", (shift_id,))
        result = cursor.fetchone()
        print(result)
        if not result:
            raise DoesntExistError(f"Shift with ID {shift_id} not found.")
        if result[0] != "open":
            raise ValueError(f"Cannot generate X Report for closed shift {shift_id}.")
        print("aq movedi")
        cursor.execute(
            """
            SELECT r.id, r.total, r.currency
            FROM receipts r
            WHERE r.shift_id = ? AND r.status = 'closed'
            """,
            (shift_id,),
        )
        print("aqac movedi vau")
        receipts = cursor.fetchall()
        print(receipts)
        n_receipts = len(receipts)
        currency_revenue = {}

        for receipt_id, total, currency in receipts:
            currency_revenue[currency] = currency_revenue.get(currency, 0) + total

        product_summary = {}
        cursor.execute(
            """
            SELECT rp.product_id, SUM(rp.quantity) AS total_quantity
            FROM receipt_products rp
            JOIN receipts r ON rp.receipt_id = r.id
            WHERE r.shift_id = ? AND r.status = 'closed'
            GROUP BY rp.product_id
            """,
            (shift_id,),
        )
        for product_id, total_quantity in cursor.fetchall():
            product_summary[product_id] = {"quantity": total_quantity}

        products = [
            {"id": pid, "quantity": data["quantity"]}
            for pid, data in product_summary.items()
        ]

        return Report(
            shift_id=shift_id,
            n_receipts=n_receipts,
            revenue=currency_revenue,
            products=products,
        )

    def get_lifetime_sales_report(self) -> SalesReport:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT r.id, r.currency, r.total
            FROM receipts r
            WHERE r.status = 'closed'
            """
        )
        receipts = cursor.fetchall()

        total_receipts = len(receipts)
        currency_totals: Dict[str, int] = {}  # Ensure float values
        closed_receipts: list[ClosedReceipt] = []

        for receipt_id, currency, total in receipts:
            currency_totals[currency] = currency_totals.get(currency, 0) + total
            closed_receipts.append(
                ClosedReceipt(receipt_id=receipt_id, calculated_payment=total)
            )

        return SalesReport(
            total_receipts=total_receipts,
            total_revenue=currency_totals,
            closed_receipts=closed_receipts,
        )
