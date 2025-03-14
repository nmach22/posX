import sqlite3
from typing import Optional

from app.core.classes.campaign_discount_calculator import CampaignDiscountCalculator
from app.core.classes.errors import AlreadyClosedError, DoesntExistError
from app.core.classes.exchange_rate_service import ExchangeRateService
from app.core.classes.percentage_discount import PercentageDiscount
from app.core.Interfaces.campaign_interface import Campaign
from app.core.Interfaces.discount_handler import DiscountHandler
from app.core.Interfaces.product_interface import Product
from app.core.Interfaces.receipt_interface import (
    AddProductRequest,
    Receipt,
    ReceiptForPayment,
    ReceiptProduct,
)
from app.core.Interfaces.receipt_repository_interface import ReceiptRepositoryInterface
from app.core.Interfaces.repository import ItemT, Repository
from app.core.Interfaces.shift_repository_interface import ShiftRepositoryInterface
from app.infra.in_memory_repositories.campaign_in_memory_repository import (
    CampaignAndProducts,
)


class ReceiptSQLRepository(ReceiptRepositoryInterface):
    def __init__(
        self,
        connection: sqlite3.Connection,
        products_repo: Repository[Product],
        shifts_repo: ShiftRepositoryInterface,
        campaigns_repo: Repository[Campaign],
        exchange_rate_service: ExchangeRateService,
        discount_handler: DiscountHandler = PercentageDiscount(),
        campaign_calculator: Optional[CampaignDiscountCalculator] = None,
    ) -> None:
        self.conn = connection
        self.products = products_repo
        self.shifts = shifts_repo
        self.campaigns = campaigns_repo
        self.exchange_rate_service = exchange_rate_service
        self._initialize_db()
        self.discount_handler = discount_handler

        if campaign_calculator is None:
            self.campaign_calculator = CampaignDiscountCalculator(discount_handler)
        else:
            self.campaign_calculator = campaign_calculator

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
                discounted_total INTEGER NOT NULL
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
            "SELECT shift_id, status FROM shifts WHERE shift_id = ?",
            (receipt.shift_id,),
        )
        row = cursor.fetchone()

        if not row:
            raise DoesntExistError(f"Shift with ID {receipt.shift_id} does not exist.")

        if row[1] == "closed":
            raise AlreadyClosedError(
                f"Shift with ID {receipt.shift_id} is already closed."
            )

        cursor.execute(
            "INSERT INTO receipts "
            "(id, shift_id, currency, status, total, discounted_total)"
            " VALUES (?, ?, ?,?,?,?)",
            (
                receipt.id,
                receipt.shift_id,
                receipt.currency.upper(),
                receipt.status,
                receipt.total,
                receipt.discounted_total,
            ),
        )

        for product in receipt.products:
            cursor.execute(
                "INSERT INTO receipt_products "
                "(receipt_id, product_id, quantity, price, total)"
                " VALUES (?, ?, ?, ?, ?)",
                (
                    receipt.id,
                    product.id,
                    product.quantity,
                    product.price,
                    product.total,
                ),
            )

        self.conn.commit()

        return receipt

    def update(self, receipt: Receipt) -> None:
        self.delete(receipt.id)
        self.create(receipt)

    def read(self, receipt_id: str) -> Receipt:
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT id, shift_id, currency, status, total, discounted_total "
            "FROM receipts WHERE id = ?",
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
                discounted_total=row[5],
            )
            return receipt
        raise DoesntExistError(f"Receipt with ID {receipt_id} does not exist.")

    def add_product_to_receipt(
        self, receipt_id: str, product_request: AddProductRequest
    ) -> Receipt:
        cursor = self.conn.cursor()

        cursor.execute("SELECT * FROM receipts WHERE id = ?", (receipt_id,))
        receipt = cursor.fetchone()

        if not receipt:
            raise DoesntExistError(f"Receipt with ID {receipt_id} does not exist.")
        elif receipt[3] == "closed":
            raise AlreadyClosedError(f"Receipt with ID {receipt_id} is already closed.")

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
            "INSERT INTO receipt_products "
            "(receipt_id, product_id, quantity, price, total)"
            " VALUES (?, ?, ?, ?, ?)",
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

        receipt = self.read(receipt_id)
        original_total = receipt.total
        products_data = receipt.products
        total_discounted_price: float = 0
        for receipt_product in products_data:
            cursor.execute(
                """
                SELECT 
                c.id, cp.campaign_id, c.type, cp.discounted_price,
                c.discount_percentage, c.buy_quantity,
                c.get_quantity, c.min_amount
                FROM campaign_products cp
                JOIN campaigns c ON cp.campaign_id = c.id
                WHERE cp.product_id = ?
                """,
                (receipt_product.id,),
            )
            campaign_rows = cursor.fetchall()

            if not campaign_rows:
                total_discounted_price += receipt_product.total
            else:
                best_discounted_price_for_this_product = receipt_product.total
                for campaign_row in campaign_rows:
                    discounted_price_using_this_campaign = (
                        self.campaign_calculator.calculate_price_for_campaign(
                            receipt_id,
                            CampaignAndProducts(
                                id=campaign_row[0],
                                campaign_id=campaign_row[1],
                                product_id=receipt_product.id,
                                discounted_price=campaign_row[3],
                            ),
                            receipt_product,
                            self,
                        )
                    )

                    best_discounted_price_for_this_product = min(
                        best_discounted_price_for_this_product,
                        discounted_price_using_this_campaign,
                    )

                total_discounted_price += best_discounted_price_for_this_product

        cursor.execute(
            """
            SELECT discount_percentage 
            FROM campaigns 
            WHERE type = 'receipt discount' 
            AND min_amount <= ?
            ORDER BY discount_percentage DESC 
            LIMIT 1
            """,
            (total_discounted_price,),
        )
        receipt_campaign = cursor.fetchone()

        if receipt_campaign:
            discount_percentage = receipt_campaign[0]
            total_discounted_price = self.discount_handler.calculate_discounted_price(
                int(total_discounted_price), discount_percentage
            )

        reduced_price = original_total - total_discounted_price
        receipt = self.read(receipt_id)
        receipt.currency = receipt.currency.upper()
        if receipt.currency != "GEL":
            conversion_rate = self.exchange_rate_service.get_exchange_rate(
                "GEL", receipt.currency
            )
            discounted_price_in_target_currency = float(
                int(total_discounted_price * conversion_rate) / 100
            )
            total_price_in_target_currency = float(
                int(original_total * conversion_rate) / 100
            )
            reduced_price_in_target_currency = float(
                int(reduced_price * conversion_rate) / 100
            )
        else:
            discounted_price_in_target_currency = float(total_discounted_price / 100)
            reduced_price_in_target_currency = float(reduced_price / 100)
            total_price_in_target_currency = float(original_total / 100)

        receipt.total = total_price_in_target_currency
        return ReceiptForPayment(
            receipt,
            discounted_price=discounted_price_in_target_currency,
            reduced_price=reduced_price_in_target_currency,
        )


    def get_campaign_with_campaign_id(self, campaign_id: str) -> Campaign | None:
        campaigns = self.campaigns.read_all()
        for campaign in campaigns:
            if campaign.campaign_id == campaign_id:
                return campaign
        return None

    def get_other_products_with_same_campaign(self, campaign_id: str) -> list[str]:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT product_id 
            FROM campaign_products 
            WHERE campaign_id = ?
            """,
            (campaign_id,),
        )
        return [row[0] for row in cursor.fetchall()]

    def product_not_in_receipt(self, product_id: str, receipt_id: str) -> bool:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT * FROM receipt_products 
            WHERE receipt_id = ? AND product_id = ?
            """,
            (receipt_id, product_id),
        )
        return cursor.fetchone() is None

    def add_payment(self, receipt_id: str) -> ReceiptForPayment:
        cursor = self.conn.cursor()

        cursor.execute("SELECT * FROM receipts WHERE id = ?", (receipt_id,))
        receipt = cursor.fetchone()

        if not receipt:
            raise DoesntExistError(f"Receipt with ID {receipt_id} does not exist.")

        receipt_for_payment = self.calculate_payment(receipt_id)
        discounted_price = receipt_for_payment.discounted_price
        cursor.execute(
            "UPDATE receipts SET discounted_total = ? WHERE id = ?",
            (discounted_price, receipt_id),
        )
        self.conn.commit()
        receipt = receipt_for_payment.receipt
        receipt_for_payment.receipt = receipt

        return receipt_for_payment

    def read_all(self) -> list[ItemT]:
        raise NotImplementedError("Not implemented yet.")
