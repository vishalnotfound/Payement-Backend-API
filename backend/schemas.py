# backend/schemas.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class UserCreate(BaseModel):
    name: str
    upi_id: str
    password: str
    balance: Optional[float] = 1000.0

class Token(BaseModel):
    access_token: str
    token_type: str

class SendRequest(BaseModel):
    to_upi: str
    amount: float

class BalanceOut(BaseModel):
    upi_id: str
    balance: float

class TransactionOut(BaseModel):
    sender_upi: str
    receiver_upi: str
    amount: float
    created_at: datetime
