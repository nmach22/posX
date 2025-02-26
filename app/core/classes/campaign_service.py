import uuid
from dataclasses import dataclass

from app.core.Interfaces.campaign_interface import (
    CampaignInterface,
    Campaign,
    CampaignRequest,
)
from app.core.Interfaces.campaign_repository_interface import (
    CampaignRepositoryInterface,
)
from app.infra.product_in_memory_repository import DoesntExistError


@dataclass
class CampaignService(CampaignInterface):
    repository: CampaignRepositoryInterface

    def create_campaign(self, campaign_request: CampaignRequest) -> Campaign:
        campaign_id = uuid.uuid4()
        new_campaign = Campaign(
            str(campaign_id), campaign_request.type, campaign_request.data
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
