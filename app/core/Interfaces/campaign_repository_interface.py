from typing import Protocol

from app.core.Interfaces.campaign_interface import Campaign


class CampaignRepositoryInterface(Protocol):
    def add_campaign(self, campaign: Campaign) -> Campaign:
        pass

    def delete_campaign(self, campaign_id: str) -> None:
        pass

    def get_all_campaigns(self) -> list[Campaign]:
        pass
