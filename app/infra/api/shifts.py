from http.client import HTTPException
from typing import Protocol

from fastapi import APIRouter, Depends, HTTPException
from fastapi.requests import Request
from pydantic import BaseModel

from app.core.Interfaces.shift_interface import Shift, Report
from app.core.Interfaces.shift_repository_interface import ShiftRepositoryInterface
from app.core.classes.shift_service import ShiftService
from app.infra.in_memory_repositories.product_in_memory_repository import (
    DoesntExistError,
)

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


class NotFoundError:
    pass


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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@shifts_api.get("/x-reports")
def get_x_reports(
    shift_id: str,
    repository: ShiftRepositoryInterface = Depends(create_shift_repository),
) -> XReportResponse:
    shift_service = ShiftService(repository)
    try:
        x_response = shift_service.get_x_report(shift_id)
        return XReportResponse(x_report=x_response)
    except DoesntExistError:
        raise HTTPException(status_code=404, detail="Shift not found.")
    except ValueError:
        raise HTTPException(status_code=400, detail="Shift is closed.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@shifts_api.get("/z-reports")
def get_z_reports(
    shift_id: str,
    repository: ShiftRepositoryInterface = Depends(create_shift_repository),
) -> ZReportResponse:
    shift_service = ShiftService(repository)
    try:
        z_response = shift_service.get_z_report(shift_id)
        return ZReportResponse(z_report=z_response)
    except DoesntExistError:
        raise HTTPException(status_code=404, detail="Shift not found.")
    except ValueError:
        raise HTTPException(status_code=400, detail="Shift is closed.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
