# backend/models.py
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    upi_id = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    balance = Column(Float, default=1000.0)

    # transactions where user is sender
    transactions = relationship("Transaction", back_populates="sender")

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"))
    receiver_upi = Column(String, index=True)
    amount = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    # relationship back to sender user
    sender = relationship("User", back_populates="transactions")
