from pydantic import BaseModel

# Request models
class UserCreate(BaseModel):
    name: str
    upi_id: str
    password: str
    balance: float = 0.0

class LoginRequest(BaseModel):
    upi_id: str
    password: str

class SendMoney(BaseModel):
    to_upi: str
    amount: float

# Response models
class Token(BaseModel):
    access_token: str
    token_type: str

class BalanceResponse(BaseModel):
    upi_id: str
    balance: float

class TransactionOut(BaseModel):
    from_upi: str
    to_upi: str
    amount: float
    created_at: str | None = None
