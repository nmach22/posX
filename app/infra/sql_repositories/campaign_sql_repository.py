import uuid
import sqlite3
from dataclasses import dataclass, field
from app.core.Interfaces.campaign_interface import Campaign, Discount, Combo, BuyNGetN
from app.core.Interfaces.campaign_repository_interface import (
    CampaignRepositoryInterface,
)
from app.core.Interfaces.product_repository_interface import ProductRepositoryInterface
from app.infra.in_memory_repositories.product_in_memory_repository import (
    DoesntExistError,
)
from app.infra.sql_repositories.product_sql_repository import (
    ProductSQLRepository,
)


class CampaignSQLRepository(CampaignRepositoryInterface):
    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self.products_repo = ProductSQLRepository(db_path)

    def __post_init__(self):
        self._initialize_db()

    def _initialize_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS campaigns (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL CHECK(type IN ('buy_n_get_n', 'discount', 'combo')),
                    discount_percentage INTEGER,
                    required_quantity INTEGER,
                    free_quantity INTEGER
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
            conn.commit()

    def add_campaign(self, campaign: Campaign) -> Campaign:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            discount_percentage = (
                campaign.data.discount_percentage
                if campaign.type in ["discount", "combo"]
                else None
            )
            required_quantity = (
                campaign.data.required_quantity
                if campaign.type == "buy_n_get_n"
                else None
            )
            free_quantity = (
                campaign.data.free_quantity if campaign.type == "buy_n_get_n" else None
            )

            cursor.execute(
                """
                INSERT INTO campaigns (id, name, type, discount_percentage, required_quantity, free_quantity)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    campaign.campaign_id,
                    campaign.data.name,
                    campaign.type,
                    discount_percentage,
                    required_quantity,
                    free_quantity,
                ),
            )

            if campaign.type == "discount":
                old_price = self.products_repo.get_product(
                    campaign.data.product_id
                ).price
                discount = campaign.data.discount_percentage
                new_price = old_price - (old_price * discount / 100)
                cursor.execute(
                    """
                    INSERT INTO campaign_products (id, campaign_id, product_id, discounted_price)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        str(uuid.uuid4()),
                        campaign.campaign_id,
                        campaign.data.product_id,
                        new_price,
                    ),
                )
            elif campaign.type == "combo":
                for product_id in campaign.data.products:
                    old_price = self.products_repo.get_product(product_id).price
                    discount = campaign.data.discount_percentage
                    new_price = old_price - (old_price * discount / 100)
                    cursor.execute(
                        """
                        INSERT INTO campaign_products (id, campaign_id, product_id, discounted_price)
                        VALUES (?, ?, ?, ?)
                        """,
                        (
                            str(uuid.uuid4()),
                            campaign.campaign_id,
                            product_id,
                            new_price,
                        ),
                    )
            elif campaign.type == "buy_n_get_n":
                cursor.execute(
                    """
                    INSERT INTO campaign_products (id, campaign_id, product_id, discounted_price)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        str(uuid.uuid4()),
                        campaign.campaign_id,
                        campaign.data.product_id,
                        self.products_repo.get_product(campaign.data.product_id).price,
                    ),
                )

            conn.commit()

        return campaign

    def delete_campaign(self, campaign_id: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT id FROM campaigns WHERE id = ?", (campaign_id,))
            campaign = cursor.fetchone()
            if not campaign:
                raise DoesntExistError(
                    f"Campaign with ID {campaign_id} does not exist."
                )

            cursor.execute(
                "DELETE FROM campaign_products WHERE campaign_id = ?", (campaign_id,)
            )
            cursor.execute("DELETE FROM campaigns WHERE id = ?", (campaign_id,))
            conn.commit()

    def get_all_campaigns(self) -> list[Campaign]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM campaigns")
            campaigns_data = cursor.fetchall()

            campaigns = []
            for campaign_data in campaigns_data:
                (
                    campaign_id,
                    name,
                    type_,
                    discount_percentage,
                    required_quantity,
                    free_quantity,
                    is_active,
                    created_at,
                ) = campaign_data

                cursor.execute(
                    "SELECT product_id FROM campaign_products WHERE campaign_id = ?",
                    (campaign_id,),
                )
                campaign_products_data = cursor.fetchall()
                # todo: in discount and buy n get n i assume that there is 1 in product_ids, es davcheckot
                product_ids = [product[0] for product in campaign_products_data]

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
                elif type_ == "buy_n_get_n":
                    campaign_data_obj = BuyNGetN(
                        product_id=product_ids[0],
                        buy_quantity=required_quantity,
                        get_quantity=free_quantity,
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
