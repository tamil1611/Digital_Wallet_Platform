
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class TransactionLimitUpdate(BaseModel):
    max_transaction_amount: Decimal | None = Field(
        default=None,
        gt=0,
        max_digits=15,
        decimal_places=2,
    )
    
    suspicious_amount_threshold: Decimal | None = Field(
        default=None,
        gt=0,
        max_digits=15,
        decimal_places=2,
    )

    daily_transfer_limit: Decimal | None = Field(
        default=None,
        gt=0,
        max_digits=15,
        decimal_places=2,
    )

    daily_withdrawal_limit: Decimal | None = Field(
        default=None,
        gt=0,
        max_digits=15,
        decimal_places=2,
    )

    max_transactions_per_day: int | None = Field(
        default=None,
        gt=0,
    )

    @model_validator(mode="after")
    def validate_at_least_one_field(self):
        if not self.model_fields_set:
            raise ValueError("At least one transaction limit must be provided.")

        return self


class TransactionLimitResponse(BaseModel):
    id: int
    max_transaction_amount: Decimal
    suspicious_amount_threshold: Decimal
    daily_transfer_limit: Decimal
    daily_withdrawal_limit: Decimal
    max_transactions_per_day: int
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

