from http.client import HTTPException
from typing import Protocol

from fastapi import APIRouter, Depends
from fastapi.requests import Request
from pydantic import BaseModel

from app.core.Interfaces.shift_interface import Shift, Report
from app.core.Interfaces.shift_repository_interface import ShiftRepositoryInterface
from app.core.classes.shift_service import ShiftService
from app.infra.product_in_memory_repository import ExistsError

shifts_api = APIRouter()


class _Infra(Protocol):
    def shifts(self) -> ShiftRepositoryInterface:
        pass


def create_shift_repository(request: Request) -> ShiftRepositoryInterface:
    infra: _Infra = request.app.state.infra
    return infra.shifts()


class ShiftResponse(BaseModel):
    shift: Shift


class XReportResponse(BaseModel):
    x_report: Report


class ZReportResponse(BaseModel):
    z_report: Report


@shifts_api.post(
    "",
    status_code=201,
    response_model=ShiftResponse,
)
def create_shift(
    repository: ShiftRepositoryInterface = Depends(create_shift_repository),
) -> ShiftResponse:
    shift_service = ShiftService(repository)
    try:
        created_shift = shift_service.create_shift()
        return ShiftResponse(shift=created_shift)
    except ExistsError:
        raise HTTPException()


@shifts_api.get("x-reports")
def get_x_reports(
    shift_id: str,
    repository: ShiftRepositoryInterface = Depends(create_shift_repository),
) -> XReportResponse:
    shift_service = ShiftService(repository)
    try:
        x_response = shift_service.get_x_report(shift_id)
        return XReportResponse(x_report=x_response)
    except ExistsError:
        raise HTTPException()


@shifts_api.get("z-reports")
def get_z_reports(
    shift_id: str,
    repository: ShiftRepositoryInterface = Depends(create_shift_repository),
) -> ZReportResponse:
    shift_service = ShiftService(repository)
    try:
        x_response = shift_service.get_x_report(shift_id)
        return ZReportResponse(x_report=x_response)
    except ExistsError:
        raise HTTPException()
