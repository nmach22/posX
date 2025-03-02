from copy import deepcopy
from dataclasses import dataclass, field

from app.core.Interfaces.campaign_interface import Campaign
from app.core.Interfaces.receipt_interface import (
    AddProductRequest,
    Receipt,
    ReceiptForPayment,
    ReceiptProduct,
)
from app.core.Interfaces.receipt_repository_interface import ReceiptRepositoryInterface
from app.core.Interfaces.repository import ItemT
from app.infra.in_memory_repositories.campaign_in_memory_repository import (
    CampaignInMemoryRepository,
)
from app.infra.in_memory_repositories.product_in_memory_repository import (
    AlreadyClosedError,
    DoesntExistError,
    ExistsError,
    ProductInMemoryRepository,
)
from app.infra.in_memory_repositories.shift_in_memory_repository import (
    ShiftInMemoryRepository,
)


@dataclass
class ReceiptInMemoryRepository(ReceiptRepositoryInterface):
    receipts: list[Receipt] = field(default_factory=list)
    products: ProductInMemoryRepository = field(
        default_factory=ProductInMemoryRepository
    )
    shifts: ShiftInMemoryRepository = field(default_factory=ShiftInMemoryRepository)
    campaigns_repo: CampaignInMemoryRepository = field(
        default_factory=CampaignInMemoryRepository
    )

    def create(self, receipt: Receipt) -> Receipt:
        if any(rec.id == receipt.id for rec in self.receipts):
            raise ExistsError(f"Receipt with ID {receipt.id} already exists.")

        shift_found = False
        for shift in self.shifts.read_all_shifts():
            if shift.shift_id == receipt.shift_id:
                shift_found = True
                break

        if shift_found is False:
            raise (
                DoesntExistError(f"Shift with ID {receipt.shift_id} does not exist.")
            )

        self.receipts.append(deepcopy(receipt))
        self.shifts.add_receipt_to_shift(receipt)
        return receipt

    def update(self, receipt_id: str) -> None:
        for receipt in self.receipts:
            if receipt.id == receipt_id:
                if receipt.status == "closed":
                    raise AlreadyClosedError(
                        f"Receipt with ID {receipt_id} is already closed."
                    )
                receipt.status = "closed"
                return
        raise DoesntExistError(f"Receipt with ID {receipt_id} does not exist.")

    def read(self, receipt_id: str) -> Receipt:
        for receipt in self.receipts:
            if receipt.id == receipt_id:
                return receipt
        raise DoesntExistError(f"Receipt with ID {receipt_id} does not exist.")

    def add_product_to_receipt(
        self, receipt_id: str, product_request: AddProductRequest
    ) -> Receipt:
        product_price = 0
        product_found = False
        for product in self.products.read_all():
            if product.id == product_request.product_id:
                product_price = product.price
                product_found = True
                break

        if product_found is False:
            raise (
                DoesntExistError(
                    f"Product with ID {product_request.product_id} does not exist."
                )
            )

        for receipt in self.receipts:
            if receipt.id == receipt_id:
                total_price = product_request.quantity * product_price

                product = ReceiptProduct(
                    id=product_request.product_id,
                    quantity=product_request.quantity,
                    price=product_price,
                    total=total_price,
                )

                receipt.products.append(deepcopy(product))
                receipt.total += total_price

                return receipt
        raise DoesntExistError(f"Receipt with ID {receipt_id} does not exist.")

    def calculate_payment(
        self,
        receipt_id: str,
    ) -> ReceiptForPayment:
        already_checkouted_product_from_combo: dict[
            str, int
        ] = {}  # {product_id: discount_percentage}
        discounted_price = 0
        receipt = self.read(receipt_id)
        receipt_products_from_receipt = receipt.products
        campaigns_and_products = self.campaigns_repo.campaigns_product_list
        for receipt_product in receipt_products_from_receipt:
            if (
                already_checkouted_product_from_combo.get(receipt_product.id)
                is not None
            ):
                discounted_price += receipt_product.total - int(
                    receipt_product.total
                    * already_checkouted_product_from_combo.get(
                        receipt_product.id, 0
                    )  # Default 0
                    / 100
                )

                continue

            campaign_without_type_on_this_product = campaigns_and_products[
                receipt_product.id
            ]
            if campaign_without_type_on_this_product is None:
                discounted_price += receipt_product.total
            else:
                campaign_with_type_on_this_product = self.get_campaign_with_campaign_id(
                    campaign_without_type_on_this_product.campaign_id
                )
                if campaign_with_type_on_this_product.type == "discount":
                    new_price = receipt_product.total - (
                        (
                            receipt_product.total
                            * campaign_with_type_on_this_product.data.discount_percentage
                        )
                        / 100
                    )
                    discounted_price += new_price
                elif campaign_with_type_on_this_product.type == "buy n get n":
                    n = campaign_with_type_on_this_product.data.buy_quantity
                    m = campaign_with_type_on_this_product.data.get_quantity
                    amount_of_campaign_costumer_use = receipt_product.quantity // (
                        n + m
                    )
                    amount_of_product_got_without_price = (
                        m * amount_of_campaign_costumer_use
                    )
                    discounted_price += receipt_product.total - (
                        receipt_product.price * amount_of_product_got_without_price
                    )
                elif campaign_with_type_on_this_product.type == "combo":
                    other_products_in_combo = (
                        self.get_other_products_with_same_campaign(
                            campaign_without_type_on_this_product.campaign_id
                        )
                    )
                    other_products_in_combo.remove(
                        campaign_without_type_on_this_product.product_id
                    )
                    skip_receipt_product = False

                    for next_product_id_in_combo in other_products_in_combo:
                        if self.product_not_in_receipt(
                            next_product_id_in_combo, receipt_id
                        ):
                            discounted_price += receipt_product.total
                            skip_receipt_product = True
                            break

                    if skip_receipt_product:
                        continue

                    discount_percentage = (
                        campaign_with_type_on_this_product.data.discount_percentage
                    )
                    discounted_price += receipt_product.total - (
                        receipt_product.total * discount_percentage / 100
                    )
                    for next_product_id_in_combo in other_products_in_combo:
                        already_checkouted_product_from_combo[
                            next_product_id_in_combo
                        ] = discount_percentage

        for campaign in self.campaigns_repo.campaigns:
            if (
                campaign.type == "receipt discount"
                and discounted_price >= campaign.data.min_amount
            ):
                discounted_price -= (
                    discounted_price * campaign.data.discount_percentage / 100
                )
                break

        return ReceiptForPayment(
            receipt, discounted_price, receipt.total - discounted_price
        )

    def delete(self, receipt_id: str) -> None:
        raise NotImplementedError("Not implemented yet.")

    def read_all(self) -> list[Receipt]:
        raise NotImplementedError("Not implemented yet.")


    def get_campaign_with_campaign_id(self, campaign_id: str) -> Campaign | None:
        for campaign in self.campaigns_repo.campaigns:
            if campaign.campaign_id == campaign_id:
                return campaign

        return None

    def get_other_products_with_same_campaign(self, campaign_id: str) -> list[str]:
        result_list: list[str] = []
        for (
            product_id,
            campaign_product,
        ) in self.campaigns_repo.campaigns_product_list.items():
            if campaign_product.campaign_id == campaign_id:
                result_list.append(product_id)

        return result_list

    def product_not_in_receipt(self, product_id: str, receipt_id: str) -> bool:
        receipt = self.read(receipt_id)
        receipt_products_from_receipt = receipt.products
        for receipt_product in receipt_products_from_receipt:
            if receipt_product.id == product_id:
                return False
        return True
