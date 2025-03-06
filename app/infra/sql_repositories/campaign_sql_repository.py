import sqlite3
import uuid
from typing import Union

from app.core.Interfaces.campaign_interface import (
    BuyNGetN,
    Campaign,
    Combo,
    Discount,
    ReceiptDiscount,
)
from app.core.Interfaces.product_interface import Product
from app.core.Interfaces.repository import Repository
from app.infra.in_memory_repositories.product_in_memory_repository import (
    DoesntExistError,
)


class CampaignSQLRepository(Repository[Campaign]):
    def __init__(
        self, connection: sqlite3.Connection, products_repo: Repository[Product]
    ) -> None:
        self.conn = connection
        self.products = products_repo
        self._initialize_db()

    def _initialize_db(self) -> None:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS campaigns (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL CHECK (
                    type IN 
                        (
                            'buy n get n', 'discount', 'combo', 'receipt discount'
                        )
                    ),
                discount_percentage INTEGER,
                buy_quantity INTEGER,
                get_quantity INTEGER,
                min_amount INTEGER
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS campaign_products (
                id TEXT PRIMARY KEY,
                campaign_id TEXT,
                product_id TEXT,
                discounted_price INTEGER,
                FOREIGN KEY (campaign_id) REFERENCES campaigns(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
            """
        )
        self.conn.commit()

    def create(self, campaign: Campaign) -> Campaign:
        cursor = self.conn.cursor()

        discount_percentage = (
            campaign.data.discount_percentage
            if campaign.type in ["discount", "combo", "receipt discount"]
            and (
                isinstance(campaign.data, Discount)
                or isinstance(campaign.data, ReceiptDiscount)
                or isinstance(campaign.data, Combo)
            )
            else None
        )
        buy_quantity = (
            campaign.data.buy_quantity
            if campaign.type == "buy n get n" and isinstance(campaign.data, BuyNGetN)
            else None
        )
        get_quantity = (
            campaign.data.get_quantity
            if campaign.type == "buy n get n" and isinstance(campaign.data, BuyNGetN)
            else None
        )

        min_amount = (
            campaign.data.min_amount
            if campaign.type == "receipt discount"
            and isinstance(campaign.data, ReceiptDiscount)
            else None
        )

        cursor.execute(
            """
            INSERT INTO campaigns (
                id, type, discount_percentage, buy_quantity, get_quantity, min_amount
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                campaign.campaign_id,
                campaign.type,
                discount_percentage,
                buy_quantity,
                get_quantity,
                min_amount,
            ),
        )

        if campaign.type == "discount" and isinstance(campaign.data, Discount):
            old_price = self.products.read(campaign.data.product_id).price
            discount = campaign.data.discount_percentage
            new_price = old_price - (old_price * discount / 100)
            cursor.execute(
                """
                INSERT INTO campaign_products 
                    (id, campaign_id, product_id, discounted_price)
                VALUES (?, ?, ?, ?)
                """,
                (
                    str(uuid.uuid4()),
                    campaign.campaign_id,
                    campaign.data.product_id,
                    new_price,
                ),
            )
        elif campaign.type == "combo" and isinstance(campaign.data, Combo):
            for product_id in campaign.data.products:
                old_price = self.products.read(product_id).price
                discount = campaign.data.discount_percentage
                new_price = old_price - (old_price * discount / 100)
                cursor.execute(
                    """
                    INSERT INTO campaign_products 
                        (id, campaign_id, product_id, discounted_price)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        str(uuid.uuid4()),
                        campaign.campaign_id,
                        product_id,
                        new_price,
                    ),
                )
        elif campaign.type == "buy n get n" and isinstance(campaign.data, BuyNGetN):
            cursor.execute(
                """
                INSERT INTO campaign_products 
                    (id, campaign_id, product_id, discounted_price)
                VALUES (?, ?, ?, ?)
                """,
                (
                    str(uuid.uuid4()),
                    campaign.campaign_id,
                    campaign.data.product_id,
                    self.products.read(campaign.data.product_id).price,
                ),
            )

        self.conn.commit()

        return campaign

    def delete(self, campaign_id: str) -> None:
        cursor = self.conn.cursor()

        cursor.execute("SELECT id FROM campaigns WHERE id = ?", (campaign_id,))
        campaign = cursor.fetchone()
        if not campaign:
            raise DoesntExistError(f"Campaign with ID {campaign_id} does not exist.")
        print("i am deleting")
        cursor.execute(
            "DELETE FROM campaign_products WHERE campaign_id = ?", (campaign_id,)
        )
        cursor.execute("DELETE FROM campaigns WHERE id = ?", (campaign_id,))
        self.conn.commit()

    def read_all(self) -> list[Campaign]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM campaigns")
        campaigns_data = cursor.fetchall()

        campaigns = []
        for campaign_data in campaigns_data:
            (
                campaign_id,
                type_,
                discount_percentage,
                buy_quantity,
                get_quantity,
                min_amount,
            ) = campaign_data

            cursor.execute(
                "SELECT product_id FROM campaign_products WHERE campaign_id = ?",
                (campaign_id,),
            )
            campaign_products_data = cursor.fetchall()
            # todo: in discount and buy n get n i assume that there is 1 in product_ids,
            #  es davcheckot
            product_ids = [product[0] for product in campaign_products_data]

            campaign_data_obj: Union[Discount, Combo, BuyNGetN, ReceiptDiscount]

            if type_ == "discount":
                campaign_data_obj = Discount(
                    product_id=product_ids[0],
                    discount_percentage=discount_percentage,
                )
            elif type_ == "combo":
                campaign_data_obj = Combo(
                    products=product_ids,
                    discount_percentage=discount_percentage,
                )
            elif type_ == "buy n get n":
                campaign_data_obj = BuyNGetN(
                    product_id=product_ids[0],
                    buy_quantity=buy_quantity,
                    get_quantity=get_quantity,
                )
            elif type_ == "receipt discount":
                campaign_data_obj = ReceiptDiscount(
                    min_amount=min_amount,
                    discount_percentage=discount_percentage,
                )
            else:
                raise DoesntExistError(f"Unknown campaign type {type_}")

            campaign = Campaign(
                campaign_id=campaign_id,
                type=type_,
                data=campaign_data_obj,
            )

            campaigns.append(campaign)

        return campaigns

    def read(self, campaign_id: str) -> Campaign:
        raise NotImplementedError("Not implemented yet.")

    def update(self, campaign: Campaign) -> None:
        raise NotImplementedError("Not implemented yet.")
