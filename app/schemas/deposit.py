from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.deposit import DepositStatus


class DepositCreate(BaseModel):
    amount: Decimal = Field(
        ...,
        gt=0,
        max_digits=18,
        decimal_places=2,
        description="Deposit amount must be greater than zero",
    )


class DepositResponse(BaseModel):
    id: int
    wallet_id: int
    amount: Decimal
    currency: str
    status: DepositStatus
    reference_number: str
    created_at: datetime
    completed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

