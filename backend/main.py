from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from passlib.context import CryptContext
from pydantic import BaseModel

# -------------------- Database --------------------
DATABASE_URL = "sqlite:///./payments.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# -------------------- Password hashing --------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# -------------------- Models --------------------
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    upi_id = Column(String, unique=True, index=True)
    balance = Column(Float, default=1000.0)

    transactions = relationship("Transaction", back_populates="owner")


class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"))
    receiver_upi = Column(String)
    amount = Column(Float)
    owner = relationship("User", back_populates="transactions")


Base.metadata.create_all(bind=engine)

# -------------------- FastAPI --------------------
app = FastAPI()

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Use specific origin in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------- Helpers --------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# -------------------- Schemas --------------------
class UserCreate(BaseModel):
    username: str
    password: str
    upi_id: str

class SendRequest(BaseModel):
    sender_upi: str
    receiver_upi: str
    amount: float

# -------------------- Routes --------------------
@app.get("/")
def read_root():
    return {"message": "Backend is running ✅"}

@app.post("/signup")
def signup(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username exists")
    hashed_pw = get_password_hash(user.password)
    new_user = User(username=user.username, password=hashed_pw, upi_id=user.upi_id)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": f"Account created for {user.username}", "upi_id": user.upi_id}

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    return {"message": "Login successful", "username": user.username, "upi_id": user.upi_id}

@app.get("/balance/{upi_id}")
def get_balance(upi_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.upi_id == upi_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"upi_id": user.upi_id, "balance": user.balance}

@app.post("/send")
def send_money(data: SendRequest, db: Session = Depends(get_db)):
    sender = db.query(User).filter(User.upi_id == data.sender_upi).first()
    receiver = db.query(User).filter(User.upi_id == data.receiver_upi).first()
    if not sender or not receiver:
        raise HTTPException(status_code=404, detail="Invalid UPI ID(s)")
    if sender.balance < data.amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    sender.balance -= data.amount
    receiver.balance += data.amount
    transaction = Transaction(sender_id=sender.id, receiver_upi=receiver.upi_id, amount=data.amount)
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return {"message": f"₹{data.amount} sent from {sender.upi_id} to {receiver.upi_id}"}

@app.get("/transactions")
def get_transactions(db: Session = Depends(get_db)):
    return db.query(Transaction).all()
