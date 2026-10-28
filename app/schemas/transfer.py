
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.transfer import TransferStatus


class TransferCreate(BaseModel):
    sender_wallet_id: int = Field(gt=0)
    receiver_wallet_id: int = Field(gt=0)
    amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2)

    @model_validator(mode="after")
    def validate_wallets(self):
        if self.sender_wallet_id == self.receiver_wallet_id:
            raise ValueError("Cannot transfer money to the same wallet")
        return self


class TransferResponse(BaseModel):
    id: int
    sender_wallet_id: int
    receiver_wallet_id: int
    amount: Decimal
    currency: str
    status: TransferStatus
    reference: str
    created_at: datetime
    completed_at: datetime | None

    model_config = ConfigDict(from_attributes=True)

