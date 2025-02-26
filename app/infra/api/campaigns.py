from typing import Any

from fastapi import APIRouter, Depends
from mypy.semanal_shared import Protocol
from pydantic import BaseModel
from starlette.requests import Request

from app.core.Interfaces.campaign_interface import (
    CampaignInterface,
    CampaignRequest,
    Campaign,
)
from app.core.Interfaces.campaign_repository_interface import (
    CampaignRepositoryInterface,
)
from app.core.classes.campaign_service import CampaignService

campaigns_api = APIRouter()


class _Infra(Protocol):
    def campaigns(self) -> CampaignRepositoryInterface:
        pass


def create_campaigns_repository(request: Request) -> CampaignRepositoryInterface:
    infra: _Infra = request.app.state.infra
    return infra.campaigns()


class ResponseCampaign(BaseModel):
    campaign: Campaign


@campaigns_api.post("", status_code=201, response_model=ResponseCampaign)
def add_campaign(
    request: CampaignRequest,
    repository: CampaignRepositoryInterface = Depends(create_campaigns_repository),
) -> ResponseCampaign:
    campaign_service = CampaignService(repository)
    created_campaign = campaign_service.create_campaign(request)
    return ResponseCampaign(campaign=created_campaign)


@campaigns_api.delete("{campaign_id}")
def delete_campaign(
    campaign_id: str,
    repository: CampaignRepositoryInterface = Depends(create_campaigns_repository),
) -> dict[Any, Any]:
    campaign_service = CampaignService(repository)
    campaign_service.delete_campaign(campaign_id)

    return {}
