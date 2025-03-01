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
        # for field in ["buy_n_get_n", "discount", "combo", "receipt_discount"]:
        value = getattr(campaign_request, campaign_request.type)
        if value is not None:
            # if campaign_data is not None:
            #     raise ValueError(
            #         "Only one type of campaign data should be provided."
            #     )
            campaign_data = value

        if campaign_data is None:
            raise ValueError("At least one campaign data field must be provided.")

        # Create the campaign using the extracted data
        new_campaign = Campaign(
            str(campaign_id),
            campaign_request.type,
            campaign_data,  # Now this is the actual campaign data object
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
