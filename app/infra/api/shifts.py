from typing import Dict, Protocol

from fastapi import APIRouter, Depends, HTTPException
from fastapi.requests import Request
from pydantic import BaseModel

from app.core.classes.shift_service import ShiftService
from app.core.Interfaces.shift_interface import Report, Shift
from app.core.Interfaces.shift_repository_interface import ShiftRepositoryInterface
from app.infra.api.products import ErrorResponse
from app.infra.in_memory_repositories.product_in_memory_repository import (
    DoesntExistError,
)
from app.infra.in_memory_repositories.shift_in_memory_repository import OpenReceiptsError

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


class CloseShiftResponse(BaseModel):
    message: str


class ClosedReceiptResponse(BaseModel):
    receipt_id: str
    calculated_payment: int


class SalesReportResponse(BaseModel):
    total_receipts: int
    total_revenue: Dict[str, int]
    closed_receipts: list[ClosedReceiptResponse]


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


@shifts_api.get(
    "/x-reports",
    responses={
        409: {
            "model": ErrorResponse,
            "description": "Product with the given barcode already exists.",
        },
        404: {"model": ErrorResponse, "description": "Product not found."},
    },
)
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

@shifts_api.post(
    "/close-shift",
    responses={
        409: {
            "model": ErrorResponse,
            "description": "Product with the given barcode already exists.",
        },
        404: {"model": ErrorResponse, "description": "Product not found."},
        400: {
            "model": ErrorResponse,
            "description": "Invalid request: shift already closed or has open receipts.",
        },
    },
)
def close_shift(
    shift_id: str,
    repository: ShiftRepositoryInterface = Depends(create_shift_repository),
) -> CloseShiftResponse:
    shift_service = ShiftService(repository)
    try:
        shift_service.close_shift(shift_id)
    except DoesntExistError:
        raise HTTPException(
            status_code=404,
            detail={"error": {"message": f"Shift with id<{shift_id}> does not exist."}},
        )
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {"message": f"Shift with id<{shift_id}> is already closed."}
            },
        )
    except OpenReceiptsError:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "message": f"Shift with id<{shift_id}> has open receipts."
                }
            },
        )

    return CloseShiftResponse(message=f"Shift {shift_id} successfully closed.")

@shifts_api.get("/sales", response_model=SalesReportResponse)
def get_sales_report(
    repository: ShiftRepositoryInterface = Depends(create_shift_repository),
) -> SalesReportResponse:
    shift_service = ShiftService(repository)
    try:
        report = shift_service.get_lifetime_sales_report()
        return SalesReportResponse(
            total_receipts=report.total_receipts,
            total_revenue=report.total_revenue,
            closed_receipts=[
                ClosedReceiptResponse(
                    receipt_id=receipt.receipt_id,
                    calculated_payment=receipt.calculated_payment,
                )
                for receipt in report.closed_receipts
            ],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
