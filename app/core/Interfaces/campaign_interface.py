from dataclasses import dataclass
from typing import Protocol


@dataclass
class Campaign:
    id: str
    campaign_type: str






class CampaignInterface(Protocol):
    def create_campaign(self, campaign_type: str) -> Campaign:
        pass

    def delete_campaign(self, campaign_id: str) -> None:
        pass

    def read_all_campaigns(self) -> list[Campaign]:
        pass