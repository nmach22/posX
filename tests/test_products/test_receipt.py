import uuid
import pytest

from app.core.Interfaces.campaign_interface import (
    Campaign,
    Discount,
    BuyNGetN,
    ReceiptDiscount,
    Combo,
)
from app.core.Interfaces.shift_interface import Shift
from app.core.classes.receipt_service import ReceiptService
from app.core.Interfaces.product_interface import Product
from app.core.Interfaces.receipt_interface import AddProductRequest, Receipt

from app.infra.in_memory_repositories.product_in_memory_repository import (
    DoesntExistError,
    ProductInMemoryRepository,
    AlreadyClosedError,
)

from app.infra.in_memory_repositories.campaign_in_memory_repository import (
    CampaignAndProducts,
    CampaignInMemoryRepository,
)

from app.infra.in_memory_repositories.receipt_in_memory_repository import (
    ReceiptInMemoryRepository,
)

from app.infra.in_memory_repositories.shift_in_memory_repository import (
    ShiftInMemoryRepository,
)


@pytest.fixture
def setup_receipt_service():
    receipt_list: list[Receipt] = []
    shift_id = "random_shift_id"
    shift_list: list[Shift] = [Shift(shift_id=shift_id, receipts=[], status="open")]
    product_list: list[Product] = [Product("123", "sigareti", 10, "12345")]

    service = ReceiptService(
        ReceiptInMemoryRepository(
            products=ProductInMemoryRepository(product_list),
            receipts=receipt_list,
            shifts=ShiftInMemoryRepository(shift_list),
        )
    )
    return service, shift_id, receipt_list


def test_should_add_receipt_in_memory(setup_receipt_service):
    service, shift_id, receipt_list = setup_receipt_service
    service.create_receipt(shift_id, currency="gel")

    assert len(receipt_list) == 1
    assert receipt_list[0].status == "open"
    assert receipt_list[0].shift_id == shift_id
    assert len(receipt_list[0].products) == 0
    assert receipt_list[0].total == 0


def test_should_close_receipt_in_memory(setup_receipt_service):
    service, shift_id, receipt_list = setup_receipt_service
    receipt = service.create_receipt(shift_id, currency="gel")
    receipt_id = receipt.id

    assert receipt.status == "open"
    service.close_receipt(receipt_id)
    assert receipt_list[0].status == "closed"


def test_should_read_receipt_in_memory(setup_receipt_service):
    service, shift_id, _ = setup_receipt_service
    receipt = service.create_receipt(shift_id, currency="gel")
    receipt_id = receipt.id

    retrieved_receipt = service.read_receipt(receipt_id)
    assert retrieved_receipt is not None
    assert retrieved_receipt.id == receipt_id
    assert retrieved_receipt.status == "open"
    assert retrieved_receipt.shift_id == shift_id
    assert retrieved_receipt.products == []
    assert retrieved_receipt.total == 0


def test_should_add_product_to_receipt(setup_receipt_service):
    service, shift_id, _ = setup_receipt_service
    receipt = service.create_receipt(shift_id, currency="gel")
    receipt_id = receipt.id

    product_request = AddProductRequest(product_id="123", quantity=2)
    updated_receipt = service.add_product(receipt_id, product_request)

    assert len(updated_receipt.products) == 1
    assert updated_receipt.products[0].id == "123"
    assert updated_receipt.products[0].quantity == 2
    assert updated_receipt.products[0].price == 10.0
    assert updated_receipt.products[0].total == 20.0
    assert updated_receipt.total == 20.0


def test_should_raise_error_when_reading_nonexistent_receipt(setup_receipt_service):
    service, _, _ = setup_receipt_service
    with pytest.raises(
        DoesntExistError, match="Receipt with ID nonexistent_id does not exist."
    ):
        service.read_receipt("nonexistent_id")


def test_should_raise_error_when_closing_nonexistent_receipt(setup_receipt_service):
    service, _, _ = setup_receipt_service
    with pytest.raises(
        DoesntExistError, match="Receipt with ID nonexistent_id does not exist."
    ):
        service.close_receipt("nonexistent_id")


def test_should_raise_error_when_adding_product_to_nonexistent_receipt(
    setup_receipt_service,
):
    service, _, _ = setup_receipt_service
    product_request = AddProductRequest(product_id="123", quantity=2)
    with pytest.raises(
        DoesntExistError, match="Receipt with ID nonexistent_id does not exist."
    ):
        service.add_product("nonexistent_id", product_request)


def test_should_raise_error_when_adding_nonexistent_product_to_receipt(
    setup_receipt_service,
):
    service, shift_id, _ = setup_receipt_service
    receipt = service.create_receipt(shift_id, currency="gel")
    receipt_id = receipt.id

    product_request = AddProductRequest(product_id="999", quantity=1)
    with pytest.raises(DoesntExistError, match="Product with ID 999 does not exist."):
        service.add_product(receipt_id, product_request)


def test_should_raise_error_when_closing_already_closed_receipt(setup_receipt_service):
    service, shift_id, _ = setup_receipt_service
    receipt = service.create_receipt(shift_id, currency="gel")
    receipt_id = receipt.id
    service.close_receipt(receipt_id)

    with pytest.raises(
        AlreadyClosedError, match=f"Receipt with ID {receipt_id} is already closed."
    ):
        service.close_receipt(receipt_id)


def test_calculate_discount_campaign():
    product_list = [
        Product(id="1", name="Product 1", price=100, barcode="12345"),
    ]
    product_repo = ProductInMemoryRepository(product_list)

    campaigns = [
        Campaign(
            campaign_id="discount_1",
            type="discount",
            data=Discount(product_id="1", discount_percentage=10),  # 10% discount
        ),
    ]
    campaigns_product_list = {
        "1": CampaignAndProducts(
            id=str(uuid.uuid4()),
            campaign_id="discount_1",
            product_id="1",
            discounted_price=90,
        )
    }
    campaign_repo = CampaignInMemoryRepository(
        product_repo, campaigns_product_list, campaigns
    )
    shift_repo = ShiftInMemoryRepository([Shift("1", [], "open")])
    receipt_repo = ReceiptInMemoryRepository(
        [], product_repo, shift_repo, campaign_repo
    )

    receipt = Receipt(id="1", shift_id="1", products=[], status="open", total=0)
    receipt_repo.add_receipt(receipt)

    product_request = AddProductRequest(product_id="1", quantity=2)  # 2 x Product 1
    receipt_repo.add_product_to_receipt("1", product_request)

    receipt_payment = receipt_repo.calculate_payment("1")

    # 2 x Product 1 at 100 each = 200
    # 10% discount -> 180
    # Additional 5% discount -> 171
    assert receipt_payment.discounted_price == 180


def test_calculate_payment_mixed_campaigns():
    # Step 1: Create product repository and add products
    product_list = [
        Product(id="1", name="Product 1", price=100, barcode="12345"),
        Product(id="2", name="Product 2", price=200, barcode="67890"),
    ]
    product_repo = ProductInMemoryRepository(product_list)

    # Step 2: Create campaign repository and add campaigns
    campaigns = [
        Campaign(
            campaign_id="discount_1",
            type="discount",
            data=Discount(
                product_id="1", discount_percentage=10
            ),  # 10% discount on Product 1
        ),
        Campaign(
            campaign_id="buy_n_get_m_1",
            type="buy n get n",
            data=BuyNGetN(
                product_id="2", buy_quantity=2, get_quantity=1
            ),  # Buy 2, Get 1 free on Product 2
        ),
        Campaign(
            campaign_id="receipt discount",
            type="receipt discount",
            data=ReceiptDiscount(min_amount=500, discount_percentage=10),
        ),
    ]
    campaigns_product_list = {
        "1": CampaignAndProducts(
            id=str(uuid.uuid4()),
            campaign_id="discount_1",
            product_id="1",
            discounted_price=90,
        ),
        "2": CampaignAndProducts(
            id=str(uuid.uuid4()),
            campaign_id="buy_n_get_m_1",
            product_id="2",
            discounted_price=200,
        ),
    }
    campaign_repo = CampaignInMemoryRepository(
        product_repo, campaigns_product_list, campaigns
    )
    shifts = [Shift("1", [], "open")]
    shift_repo = ShiftInMemoryRepository(shifts)

    # Step 3: Create receipt repository
    receipt_repo = ReceiptInMemoryRepository(
        products=product_repo,
        shifts=shift_repo,
        campaigns_repo=campaign_repo,
    )

    # Step 4: Create a receipt and add products to it
    receipt = Receipt(
        id="1", shift_id="1", currency="gel", products=[], status="open", total=0
    )
    receipt_repo.add_receipt(receipt)

    # Add Product 1 (with 10% discount) and Product 2 (with Buy 2 Get 1 free)
    product_request_1 = AddProductRequest(product_id="1", quantity=2)  # 2 x Product 1
    product_request_2 = AddProductRequest(product_id="2", quantity=3)  # 3 x Product 2

    receipt_repo.add_product_to_receipt("1", product_request_1)
    receipt_repo.add_product_to_receipt("1", product_request_2)

    # Step 5: Calculate the discounted price
    receipt_payment = receipt_repo.calculate_payment("1")

    # Step 6: Verify the discounted price
    # Expected:
    # - Product 1: 2 x 100 = 200, with 10% discount = 180
    # - Product 2: Buy 2 Get 1 free, so 3 items cost 400 (2 x 200)
    # Total: 180 + 400 = 580
    # receipt discount: 580-58
    assert receipt_payment.discounted_price == 580 - 58


def test_calculate_payment_combo_discount_multiple_quantities():
    product_list = [
        Product(id="1", name="Product 1", price=100, barcode="12345"),
        Product(id="2", name="Product 2", price=200, barcode="67890"),
    ]
    product_repo = ProductInMemoryRepository(product_list)

    campaigns = [
        Campaign(
            campaign_id="combo_1",
            type="combo",
            data=Combo(
                products=["1", "2"], discount_percentage=20
            ),  # 20% off when bought together
        ),
    ]
    campaigns_product_list = {
        "1": CampaignAndProducts(
            id=str(uuid.uuid4()),
            campaign_id="combo_1",
            product_id="1",
            discounted_price=80,
        ),
        "2": CampaignAndProducts(
            id=str(uuid.uuid4()),
            campaign_id="combo_1",
            product_id="2",
            discounted_price=160,
        ),
    }
    campaign_repo = CampaignInMemoryRepository(
        product_repo, campaigns_product_list, campaigns
    )
    shift_repo = ShiftInMemoryRepository([Shift("1", [], "open")])
    receipt_repo = ReceiptInMemoryRepository(
        [], product_repo, shift_repo, campaign_repo
    )

    receipt = Receipt(id="1", shift_id="1", products=[], status="open", total=0)
    receipt_repo.add_receipt(receipt)

    product_request_1 = AddProductRequest(product_id="1", quantity=2)  # 2 x Product 1
    product_request_2 = AddProductRequest(product_id="2", quantity=2)  # 2 x Product 2

    receipt_repo.add_product_to_receipt("1", product_request_1)
    receipt_repo.add_product_to_receipt("1", product_request_2)

    receipt_payment = receipt_repo.calculate_payment("1")

    # 2 x Product 1 (80 each) + 2 x Product 2 (160 each) = 480
    assert receipt_payment.discounted_price == 480


def test_calculate_payment_buy_n_get_n_with_discount():
    product_list = [
        Product(id="1", name="Product 1", price=100, barcode="12345"),
    ]
    product_repo = ProductInMemoryRepository(product_list)

    campaigns = [
        Campaign(
            campaign_id="buy_n_get_1",
            type="buy n get n",
            data=BuyNGetN(product_id="1", buy_quantity=2, get_quantity=1),
        ),
    ]
    campaigns_product_list = {
        "1": CampaignAndProducts(
            id=str(uuid.uuid4()),
            campaign_id="buy_n_get_1",
            product_id="1",
            discounted_price=100,
        ),
    }
    campaign_repo = CampaignInMemoryRepository(
        product_repo, campaigns_product_list, campaigns
    )
    shift_repo = ShiftInMemoryRepository([Shift("1", [], "open")])
    receipt_repo = ReceiptInMemoryRepository(
        [], product_repo, shift_repo, campaign_repo
    )

    receipt = Receipt(id="1", shift_id="1", products=[], status="open", total=0)
    receipt_repo.add_receipt(receipt)

    product_request = AddProductRequest(product_id="1", quantity=3)  # Buy 3 (one free)
    receipt_repo.add_product_to_receipt("1", product_request)

    receipt_payment = receipt_repo.calculate_payment("1")

    # Buy 2 Get 1 Free: 2 x 100 = 200
    # 10% discount: 200 - 20 = 180
    assert receipt_payment.discounted_price == 200


def test_calculate_payment_large_receipt_discount():
    product_list = [
        Product(id="1", name="Product 1", price=150, barcode="12345"),
        Product(id="2", name="Product 2", price=250, barcode="67890"),
    ]
    product_repo = ProductInMemoryRepository(product_list)

    campaigns = [
        Campaign(
            campaign_id="discount_1",
            type="discount",
            data=Discount(product_id="1", discount_percentage=10),  # 10% discount
        ),
        Campaign(
            campaign_id="buy_n_get_1",
            type="buy n get n",
            data=BuyNGetN(
                product_id="2", buy_quantity=2, get_quantity=1
            ),  # Buy 2 Get 1 Free
        ),
        Campaign(
            campaign_id="receipt_discount_1",
            type="receipt discount",
            data=ReceiptDiscount(
                min_amount=500, discount_percentage=15
            ),  # 15% discount on total >= 500
        ),
    ]
    campaigns_product_list = {
        "1": CampaignAndProducts(
            id=str(uuid.uuid4()),
            campaign_id="discount_1",
            product_id="1",
            discounted_price=135,
        ),
        "2": CampaignAndProducts(
            id=str(uuid.uuid4()),
            campaign_id="buy_n_get_1",
            product_id="2",
            discounted_price=250,
        ),
    }
    campaign_repo = CampaignInMemoryRepository(
        product_repo, campaigns_product_list, campaigns
    )
    shift_repo = ShiftInMemoryRepository([Shift("1", [], "open")])
    receipt_repo = ReceiptInMemoryRepository(
        [], product_repo, shift_repo, campaign_repo
    )

    receipt = Receipt(id="1", shift_id="1", products=[], status="open", total=0)
    receipt_repo.add_receipt(receipt)

    product_request_1 = AddProductRequest(product_id="1", quantity=2)  # 2 x Product 1
    product_request_2 = AddProductRequest(
        product_id="2", quantity=3
    )  # 3 x Product 2 (Buy 2 Get 1)

    receipt_repo.add_product_to_receipt("1", product_request_1)
    receipt_repo.add_product_to_receipt("1", product_request_2)

    receipt_payment = receipt_repo.calculate_payment("1")

    # 2 x 135 = 270 (Discounted Product 1)
    # 2 x 250 = 500 (Buy 2 Get 1 Product 2)
    # Total: 770
    # 15% receipt discount: 770 - 115.5 = 654.5
    assert receipt_payment.discounted_price == 654.5
