
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

class TransactionCreate(BaseModel):
    wallet_id: int = Field(..., gt=0)

    transaction_type: str = Field(
        ...,
        pattern="^(DEPOSIT|WITHDRAWAL|TRANSFER|REFUND)$",
    )

    amount: Decimal = Field(
        ...,
        gt=0,
        max_digits=18,
        decimal_places=2,
    )

    description: str | None = Field(
        default=None,
        max_length=255,
    )
class TransactionResponse(BaseModel):
   id: int
   wallet_id: int
   transaction_type: str
   amount: Decimal
   balance_before: Decimal | None = None
   balance_after: Decimal | None = None
   status: str
   reference_entity: str | None = None
   reference_id: str | None = None
   description: str | None = None
   created_by: int | None = None
   created_at: datetime


model_config = ConfigDict(from_attributes=True)

