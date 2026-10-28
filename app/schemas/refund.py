from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints
from typing import Annotated

RefundReason = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=3, max_length=500),
    ]

class RefundCreate(BaseModel):
   original_transaction_id: int = Field(gt=0)
   amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2)
   reason: RefundReason

class RefundResponse(BaseModel):
   id: int
   original_transaction_id: int
   wallet_id: int
   requested_by: int
   reviewed_by: int | None
   amount: Decimal
   status: str
   reason: str
   rejection_reason: str | None
   created_at: datetime
   reviewed_at: datetime | None
   completed_at: datetime | None


model_config = ConfigDict(from_attributes=True)


class RefundReject(BaseModel):
  rejection_reason: Annotated[
   str,
   StringConstraints(strip_whitespace=True, min_length=3, max_length=500),
   ]
