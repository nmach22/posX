import sqlite3
from app.core.Interfaces.receipt_interface import (
    AddProductRequest,
    Receipt,
    ReceiptProduct,
)
from app.core.Interfaces.receipt_repository_interface import ReceiptRepositoryInterface
from app.infra.sql_repositories.campaign_sql_repository import CampaignSQLRepository
from app.infra.in_memory_repositories.product_in_memory_repository import (
    DoesntExistError,
    ExistsError,
)
from app.infra.sql_repositories.product_sql_repository import ProductSQLRepository
from app.infra.sql_repositories.shift_sql_repository import ShiftSQLRepository


class ReceiptSQLRepository(ReceiptRepositoryInterface):
    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self.products = ProductSQLRepository(db_path)
        self.shifts = ShiftSQLRepository(db_path)
        self.campaigns = CampaignSQLRepository(db_path)
        self._initialize_db()

    def _initialize_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS receipts (
                    id TEXT PRIMARY KEY,
                    shift_id TEXT NOT NULL,
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
            conn.commit()

    def add_receipt(self, receipt: Receipt) -> Receipt:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id FROM receipts WHERE id = ?",
                (receipt.id,),
            )
            if cursor.fetchone():
                raise ExistsError(f"Receipt with ID {receipt.id} already exists.")

            cursor.execute(
                "INSERT INTO receipts (id, shift_id, status, total) VALUES (?, ?, ?,?)",
                (receipt.id, receipt.shift_id, receipt.status, receipt.total),
            )
            conn.commit()

        # self.shifts.add_receipt_to_shift(receipt)
        return receipt

    def close_receipt(self, receipt_id: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT status FROM receipts WHERE id = ?",
                (receipt_id,),
            )
            row = cursor.fetchone()
            if row and row[0] == "closed":
                # todo:saxeli ar sheesabameba
                raise DoesntExistError(
                    f"Receipt with ID {receipt_id} is already closed."
                )

            cursor.execute(
                "UPDATE receipts SET status = ? WHERE id = ?",
                ("closed", receipt_id),
            )
            if cursor.rowcount == 0:
                raise DoesntExistError(f"Receipt with ID {receipt_id} does not exist.")
            conn.commit()

    def get_receipt(self, receipt_id: str) -> Receipt:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, status, total FROM receipts WHERE id = ?",
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
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
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
            conn.commit()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE receipts SET total = total + ? WHERE id = ?",
                (total_price, receipt_id),
            )
            conn.commit()

        return self.get_receipt(receipt_id)

    # def calculate_payment(self, receipt_id: str) -> ReceiptForPayment:
    #     with sqlite3.connect(self.db_path) as conn:
    #         cursor = conn.cursor()
    #         cursor.execute(
    #             """
    #             SELECT product_id, quantity, price, total
    #             FROM receipt_products
    #             WHERE receipt_id = ?
    #             """,
    #             (receipt_id,),
    #         )
    #         products = cursor.fetchall()
    #         if not products:
    #             raise DoesntExistError(
    #                 f"Receipt with ID {receipt_id} does not have any products."
    #             )
    #
    #         total_amount = sum(product[3] for product in products)
    #         receipt_payment = ReceiptForPayment(
    #             receipt=self.get_receipt(receipt_id), total_price=total_amount
    #         )
    #         return receipt_payment
