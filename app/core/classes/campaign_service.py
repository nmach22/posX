import uuid
from dataclasses import dataclass
from typing import Optional

from app.core.Interfaces.campaign_interface import (
    CampaignInterface,
    Campaign,
    CampaignRequest,
    CampaignData,
)
from app.core.Interfaces.campaign_repository_interface import (
    CampaignRepositoryInterface,
)
from app.infra.in_memory_repositories.product_in_memory_repository import (
    DoesntExistError,
)


@dataclass
class CampaignService(CampaignInterface):
    repository: CampaignRepositoryInterface

    def create_campaign(self, campaign_request: CampaignRequest) -> Campaign:
        campaign_id = uuid.uuid4()

        campaign_data: Optional[CampaignData] = None
        type_in_string: str
        if campaign_request.type == "buy n get n":
            type_in_string = "buy_n_get_n"
        elif campaign_request.type == "receipt discount":
            type_in_string = "receipt_discount"
        else:
            type_in_string = campaign_request.type

        value = getattr(campaign_request, type_in_string)

        if value is not None:
            campaign_data = value

        if campaign_data is None:
            raise ValueError("At least one campaign data field must be provided.")

        new_campaign = Campaign(
            str(campaign_id),
            campaign_request.type,
            campaign_data,
        )

        self.repository.add_campaign(new_campaign)
        return new_campaign

    def delete_campaign(self, campaign_id: str) -> None:
        try:
            self.repository.delete_campaign(campaign_id)
        except DoesntExistError:
            raise DoesntExistError

    def read_all_campaigns(self) -> list[Campaign]:
        return self.repository.get_all_campaigns()
