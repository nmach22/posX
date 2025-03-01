import sqlite3

from app.core.Interfaces.campaign_repository_interface import (
    CampaignRepositoryInterface,
)
from app.core.Interfaces.product_repository_interface import ProductRepositoryInterface
from app.core.Interfaces.receipt_interface import (
    AddProductRequest,
    Receipt,
    ReceiptForPayment,
    ReceiptProduct,
)
from app.core.Interfaces.receipt_repository_interface import ReceiptRepositoryInterface
from app.core.Interfaces.shift_repository_interface import ShiftRepositoryInterface
from app.infra.in_memory_repositories.product_in_memory_repository import (
    AlreadyClosedError,
    DoesntExistError,
)


class ReceiptSQLRepository(ReceiptRepositoryInterface):
    def __init__(
        self,
        connection: sqlite3.Connection,
        products_repo: ProductRepositoryInterface,
        shifts_repo: ShiftRepositoryInterface,
        campaigns_repo: CampaignRepositoryInterface,
    ):
        self.conn = connection
        self.products = products_repo
        self.shifts = shifts_repo
        self.campaigns = campaigns_repo
        self._initialize_db()

    def _initialize_db(self):
        cursor = self.conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS receipts (
                id TEXT PRIMARY KEY,
                shift_id TEXT NOT NULL,
                currency TEXT NOT NULL,
                status TEXT NOT NULL,
                total INTEGER NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS receipt_products (
                receipt_id TEXT,
                product_id TEXT,
                quantity INTEGER,
                price INTEGER,
                total INTEGER,
                FOREIGN KEY (receipt_id) REFERENCES receipts(id)
            )
            """
        )
        self.conn.commit()

    def add_receipt(self, receipt: Receipt) -> Receipt:
        cursor = self.conn.cursor()
        cursor.execute("SELECT shift_id FROM shifts WHERE shift_id = ?", (receipt.shift_id,))
        if not cursor.fetchone():
            raise DoesntExistError(f"Shift with ID {receipt.shift_id} does not exist.")

        cursor.execute(
            "INSERT INTO receipts (id, shift_id, currency, status, total) VALUES (?, ?, ?,?, ?)",
            (
                receipt.id,
                receipt.shift_id,
                receipt.currency,
                receipt.status,
                receipt.total,
            ),
        )
        self.conn.commit()

        # self.shifts.add_receipt_to_shift(receipt)
        return receipt

    def close_receipt(self, receipt_id: str) -> None:
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT status FROM receipts WHERE id = ?",
            (receipt_id,),
        )
        row = cursor.fetchone()
        if row and row[0] == "closed":
            raise AlreadyClosedError(f"Receipt with ID {receipt_id} is already closed.")

        cursor.execute(
            "UPDATE receipts SET status = ? WHERE id = ?",
            ("closed", receipt_id),
        )
        if cursor.rowcount == 0:
            raise DoesntExistError(f"Receipt with ID {receipt_id} does not exist.")
        self.conn.commit()

    def get_receipt(self, receipt_id: str) -> Receipt:
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT id,  currency, status, total FROM receipts WHERE id = ?",
            (receipt_id,),
        )
        row = cursor.fetchone()
        if row:
            cursor.execute(
                """
                SELECT rp.product_id, rp.quantity, rp.price, rp.total
                FROM receipt_products rp
                WHERE rp.receipt_id = ?
                """,
                (receipt_id,),
            )
            products_data = cursor.fetchall()

            products = []
            for product_data in products_data:
                product = ReceiptProduct(
                    id=product_data[0],
                    quantity=product_data[1],
                    price=product_data[2],
                    total=product_data[3],
                )
                products.append(product)

            receipt = Receipt(
                id=receipt_id,
                shift_id=row[0],
                currency=row[1],
                status=row[2],
                total=row[3],
                products=products,
            )
            return receipt
        raise DoesntExistError(f"Receipt with ID {receipt_id} does not exist.")

    def add_product_to_receipt(
        self, receipt_id: str, product_request: AddProductRequest
    ) -> Receipt:
        # product_price = 0
        cursor = self.conn.cursor()

        cursor.execute("SELECT id FROM receipts WHERE id = ?", (receipt_id,))
        if not cursor.fetchone():
            raise DoesntExistError(f"Receipt with ID {receipt_id} does not exist.")

        cursor.execute(
            "SELECT price FROM products WHERE id = ?",
            (product_request.product_id,),
        )
        row = cursor.fetchone()
        if row:
            product_price = row[0]
        else:
            raise DoesntExistError(
                f"Product with ID {product_request.product_id} does not exist."
            )

        total_price = product_request.quantity * product_price

        cursor.execute(
            "INSERT INTO receipt_products (receipt_id, product_id, quantity, price, total) VALUES (?, ?, ?, ?, ?)",
            (
                receipt_id,
                product_request.product_id,
                product_request.quantity,
                product_price,
                total_price,
            ),
        )
        self.conn.commit()

        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE receipts SET total = total + ? WHERE id = ?",
            (total_price, receipt_id),
        )
        self.conn.commit()

        return self.get_receipt(receipt_id)


def calculate_payment(self, receipt_id: str) -> ReceiptForPayment:
    cursor = self.conn.cursor()

    cursor.execute("SELECT total FROM receipts WHERE id = ?", (receipt_id,))
    row = cursor.fetchone()
    if not row:
        raise DoesntExistError(f"Receipt with ID {receipt_id} does not exist.")

    original_total = row[0]

    cursor.execute(
        """
        SELECT rp.product_id, rp.quantity, rp.price, rp.total
        FROM receipt_products rp
        WHERE rp.receipt_id = ?
        """,
        (receipt_id,),
    )
    products_data = cursor.fetchall()

    total_discounted_price = 0
    products = []

    for product_data in products_data:
        product_id, quantity, price, total_price = product_data

        cursor.execute(
            """
            SELECT c.id, c.type, cp.discounted_price, c.discount_percentage, c.required_quantity, c.free_quantity
            FROM campaign_products cp
            JOIN campaigns c ON cp.campaign_id = c.id
            WHERE cp.product_id = ?
            """,
            (product_id,),
        )
        campaign_row = cursor.fetchone()

        if campaign_row:
            (
                campaign_id,
                campaign_type,
                campaign_discounted_price,
                discount_percentage,
                required_qty,
                free_qty,
            ) = campaign_row

            if campaign_type == "discount":
                discounted_price = campaign_discounted_price
                total_discounted_price += discounted_price * quantity
            elif campaign_type == "combo":
                cursor.execute(
                    """
                    SELECT cp.product_id
                    FROM campaign_products cp
                    WHERE cp.campaign_id = ?
                    """,
                    (campaign_id,),
                )
                combo_products = [row[0] for row in cursor.fetchall()]
                receipt_products = {
                    product_id: quantity for product_id, quantity, _, _ in products_data
                }
                if all(prod in receipt_products for prod in combo_products):
                    discounted_price = campaign_discounted_price
                    total_discounted_price += discounted_price * quantity
            elif campaign_type == "buy n get n":
                if quantity >= required_qty:
                    result = quantity // (required_qty + free_qty)
                    discounted_price = result * free_qty
                    total_discounted_price += discounted_price

        reduced_price = original_total - total_discounted_price
        cursor.execute(
            """
            SELECT discount_percentage, min_amount
            FROM campaigns
            WHERE type = 'receipt discount' AND min_amount <= ?
            """,
            (reduced_price,),
        )
        receipt_discount_row = cursor.fetchone()

        if receipt_discount_row:
            discount_percentage, min_amount = receipt_discount_row
            receipt_discount_price = (reduced_price * discount_percentage) / 100
            reduced_price -= receipt_discount_price

        return ReceiptForPayment(
            receipt=self.get_receipt(receipt_id),
            discounted_price=total_discounted_price,
            reduced_price=reduced_price,
        )
