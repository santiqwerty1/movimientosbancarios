from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class Transaction:
    provider: str
    date: date
    description: str
    amount: float
    balance: Optional[float]
    currency: str
    raw_reference: Optional[str]
    source_file: str

    def as_db_tuple(self) -> tuple[str, str, str, float, Optional[float], str, Optional[str], str]:
        return (
            self.provider,
            self.date.isoformat(),
            self.description,
            self.amount,
            self.balance,
            self.currency,
            self.raw_reference,
            self.source_file,
        )
