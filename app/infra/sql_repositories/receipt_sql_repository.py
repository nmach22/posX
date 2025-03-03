import sqlite3

from app.core.Interfaces.campaign_interface import Campaign
from app.core.Interfaces.product_interface import Product
from app.core.Interfaces.receipt_interface import (
    AddProductRequest,
    Receipt,
    ReceiptForPayment,
    ReceiptProduct,
)
from app.core.Interfaces.receipt_repository_interface import ReceiptRepositoryInterface
from app.core.Interfaces.repository import Repository
from app.core.Interfaces.shift_repository_interface import ShiftRepositoryInterface
from app.core.classes.exchange_rate_service import ExchangeRateService
from app.infra.in_memory_repositories.product_in_memory_repository import (
    DoesntExistError,
)


class ReceiptSQLRepository(ReceiptRepositoryInterface):
    def __init__(
        self,
        connection: sqlite3.Connection,
        products_repo: Repository[Product],
        shifts_repo: ShiftRepositoryInterface,
        campaigns_repo: Repository[Campaign],
        exchange_rate_service: ExchangeRateService,
    ) -> None:
        self.conn = connection
        self.products = products_repo
        self.shifts = shifts_repo
        self.campaigns = campaigns_repo
        self.exchange_rate_service = exchange_rate_service
        self._initialize_db()

    def _initialize_db(self) -> None:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS receipts (
                id TEXT PRIMARY KEY,
                shift_id TEXT NOT NULL,
                currency TEXT NOT NULL,
                status TEXT NOT NULL,
                total INTEGER NOT NULL,
                total_payment INTEGER NOT NULL,
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

    def create(self, receipt: Receipt) -> Receipt:
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT shift_id FROM shifts WHERE shift_id = ?", (receipt.shift_id,)
        )
        if not cursor.fetchone():
            raise DoesntExistError(f"Shift with ID {receipt.shift_id} does not exist.")

        cursor.execute(
            "INSERT INTO receipts (id, shift_id, currency, status, total, total_payment) VALUES (?, ?, ?,?, ?)",
            (
                receipt.id,
                receipt.shift_id,
                receipt.currency,
                receipt.status,
                receipt.total,
                receipt.total_payment,
            ),
        )

        for product in receipt.products:
            cursor.execute(
                "INSERT INTO receipt_products (receipt_id, product_id, quantity, price, total) VALUES (?, ?, ?, ?, ?)",
                (
                    receipt.id,
                    product.id,
                    product.quantity,
                    product.price,
                    product.total,
                ),
            )

        self.conn.commit()

        # self.shifts.add_receipt_to_shift(receipt)
        return receipt

    def update(self, receipt: Receipt) -> None:
        self.delete(receipt.id)
        # todo:create doesnt test if receipt id already exists
        self.create(receipt)
        # cursor = self.conn.cursor()
        # cursor.execute(
        #     "UPDATE receipts SET status = ? WHERE id = ?",
        #     ("closed", receipt.id),
        # )
        # if cursor.rowcount == 0:
        #     raise DoesntExistError(f"Receipt with ID {receipt.id} does not exist.")
        # self.conn.commit()

    def read(self, receipt_id: str) -> Receipt:
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT id, shift_id, currency, status, total,total_payment FROM receipts WHERE id = ?",
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
                id=row[0],
                shift_id=row[1],
                currency=row[2],
                status=row[3],
                total=row[4],
                products=products,
                total_payment=row[5],
            )
            return receipt
        raise DoesntExistError(f"Receipt with ID {receipt_id} does not exist.")

    def add_product_to_receipt(
        self, receipt_id: str, product_request: AddProductRequest
    ) -> Receipt:
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

        return self.read(receipt_id)

    def delete(self, item_id: str) -> None:
        cursor = self.conn.cursor()

        cursor.execute("SELECT id FROM receipts WHERE id = ?", (item_id,))
        if not cursor.fetchone():
            raise DoesntExistError(f"Receipt with ID {item_id} does not exist.")

        cursor.execute("DELETE FROM receipt_products WHERE receipt_id = ?", (item_id,))

        cursor.execute("DELETE FROM receipts WHERE id = ?", (item_id,))

        self.conn.commit()

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
                        product_id: quantity
                        for product_id, quantity, _, _ in products_data
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


            receipt = self.read(receipt_id)
            if receipt.currency != "GEL":
                conversion_rate = self.exchange_rate_service.get_exchange_rate("GEL", receipt.currency)
                discounted_price_in_target_currency = total_discounted_price * conversion_rate
                reduced_price_in_target_currency = reduced_price * conversion_rate
            else:
                discounted_price_in_target_currency = total_discounted_price
                reduced_price_in_target_currency = reduced_price

            return ReceiptForPayment(
                receipt,
                discounted_price=discounted_price_in_target_currency,
                reduced_price=reduced_price_in_target_currency,
            )
