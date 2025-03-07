import uuid
from dataclasses import dataclass
from typing import Optional

from app.core.classes.errors import DoesntExistError
from app.core.Interfaces.campaign_interface import (
    Campaign,
    CampaignData,
    CampaignInterface,
    CampaignRequest,
    ReceiptDiscount,
)
from app.core.Interfaces.repository import Repository


@dataclass
class CampaignService(CampaignInterface):
    repository: Repository[Campaign]

    def create_campaign(self, campaign_request: CampaignRequest) -> Campaign:
        campaign_id = uuid.uuid4()

        campaign_data: Optional[CampaignData] = None
        type_in_string: str
        campaign_type: str = campaign_request.type.lower()
        if campaign_type == "buy n get n":
            type_in_string = "buy_n_get_n"
        elif campaign_type == "receipt discount":
            type_in_string = "receipt_discount"

        else:
            type_in_string = campaign_request.type

        value = getattr(campaign_request, type_in_string)

        if value is not None:
            campaign_data = value

        if campaign_data is None:
            raise ValueError("At least one campaign data field must be provided.")

        if campaign_type == "receipt discount" and isinstance(
            campaign_data, ReceiptDiscount
        ):
            campaign_data.min_amount *= 100

        new_campaign = Campaign(
            str(campaign_id),
            campaign_request.type,
            campaign_data,
        )

        self.repository.create(new_campaign)
        if campaign_type == "receipt discount" and isinstance(
            new_campaign.data, ReceiptDiscount
        ):
            new_campaign.data.min_amount /= 100
        return new_campaign

    def delete_campaign(self, campaign_id: str) -> None:
        try:
            self.repository.delete(campaign_id)
        except DoesntExistError:
            raise DoesntExistError

    def read_all_campaigns(self) -> list[Campaign]:
        return self.repository.read_all()
