from typing import Any, Protocol

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from starlette.requests import Request

from app.core.classes.campaign_service import CampaignService
from app.core.Interfaces.campaign_interface import (
    Campaign,
    CampaignRequest,
)
from app.core.Interfaces.repository import Repository
from app.infra.api.products import ErrorResponse
from app.infra.in_memory_repositories.product_in_memory_repository import (
    DoesntExistError,
)

campaigns_api = APIRouter()


class _Infra(Protocol):
    def campaigns(self) -> Repository[Campaign]:
        pass


def create_campaigns_repository(request: Request) -> Repository[Campaign]:
    infra: _Infra = request.app.state.infra
    return infra.campaigns()


class ResponseCampaign(BaseModel):
    campaign: Campaign


@campaigns_api.post(
    "",
    status_code=201,
    responses={404: {"model": ErrorResponse, "description": "Product not found."}},
)
def add_campaign(
    request: CampaignRequest,
    repository: Repository[Campaign] = Depends(create_campaigns_repository),
) -> ResponseCampaign:
    campaign_service = CampaignService(repository)

    try:
        created_campaign = campaign_service.create_campaign(request)
    except DoesntExistError:
        raise HTTPException(
            status_code=404,
            detail={"error": {"message": "product with this id does not exist."}},
        )
    return ResponseCampaign(campaign=created_campaign)


@campaigns_api.delete(
    "/{campaign_id}",
    responses={404: {"model": ErrorResponse, "description": "Campaign not found"}},
)
def delete_campaign(
    campaign_id: str,
    repository: Repository[Campaign] = Depends(create_campaigns_repository),
) -> dict[Any, Any]:
    campaign_service = CampaignService(repository)
    try:
        campaign_service.delete_campaign(campaign_id)
    except DoesntExistError:
        raise HTTPException(
            status_code=404,
            detail={"error": {"message": "campaign with this id does not exist."}},
        )
    return {}


class ResponseListCampaign(BaseModel):
    campaigns: list[Campaign]


@campaigns_api.get("", response_model=ResponseListCampaign)
def get_all_campaigns(
    repository: Repository[Campaign] = Depends(create_campaigns_repository),
) -> ResponseListCampaign:
    campaign_service = CampaignService(repository)
    campaigns = campaign_service.read_all_campaigns()
    print(campaigns)
    return ResponseListCampaign(
        campaigns=[
            Campaign(
                campaign_id=_campaign.campaign_id,
                type=_campaign.type,
                data=_campaign.data,
            )
            for _campaign in campaigns
        ]
    )
    pass
