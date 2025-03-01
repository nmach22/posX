from typing import Protocol

from app.core.Interfaces.campaign_interface import Campaign


class CampaignRepositoryInterface(Protocol):
    def create(self, item: Campaign) -> Campaign:
        pass

    def delete(self, item_id: str) -> None:
        pass

    def read_all(self) -> list[Campaign]:
        pass
