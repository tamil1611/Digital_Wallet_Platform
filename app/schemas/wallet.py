
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class WalletCreate(BaseModel):
    currency: str = Field(
        default="INR",
        min_length=3,
        max_length=3,
    )


class WalletUpdate(BaseModel):
    currency: str | None = Field(
        default=None,
        min_length=3,
        max_length=3,
    )


class WalletResponse(BaseModel):
    id: int
    user_id: int
    available_balance: Decimal
    pending_balance: Decimal
    currency: str
    status: Literal["ACTIVE", "FROZEN", "SUSPENDED", "CLOSED"]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

