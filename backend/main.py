import os
import logging
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session, joinedload

from database import SessionLocal, engine, Base
import models, schemas

# ...existing code...

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure tables exist
Base.metadata.create_all(bind=engine)

# Config
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Auth setup
# Use pbkdf2_sha256 to avoid bcrypt native dependency issues
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

app = FastAPI(title="Payment Backend API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500", "http://localhost:5500", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    # use numeric timestamp for exp
    to_encode.update({"exp": int(expire.timestamp())})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_user_by_upi(db: Session, upi_id: str):
    return db.query(models.User).filter(models.User.upi_id == upi_id).first()

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        upi_id: str = payload.get("sub")
        if upi_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user_by_upi(db, upi_id=upi_id)
    if user is None:
        raise credentials_exception
    return user

@app.get("/")
def root():
    return {"message": "Payment Backend API Running"}

@app.post("/signup", status_code=201)
def signup(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    try:
        logger.info("Signup request for upi_id=%s", user_in.upi_id)
        if db.query(models.User).filter(models.User.upi_id == user_in.upi_id).first():
            raise HTTPException(status_code=400, detail="UPI ID already exists")

        hashed = get_password_hash(user_in.password)
        user = models.User(
            name=user_in.name,
            upi_id=user_in.upi_id,
            hashed_password=hashed,
            balance=user_in.balance if user_in.balance is not None else 1000.0
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info("Created user %s", user.upi_id)
        return {"message": "User created", "upi_id": user.upi_id}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.exception("Signup failed")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.post("/token", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.upi_id == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user.upi_id})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/me/balance", response_model=schemas.BalanceOut)
def read_balance(current_user: models.User = Depends(get_current_user)):
    return {"upi_id": current_user.upi_id, "balance": current_user.balance}

@app.post("/me/send")
def send_money(req: schemas.SendRequest, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        sender = db.query(models.User).filter(models.User.id == current_user.id).first()
        receiver = db.query(models.User).filter(models.User.upi_id == req.to_upi).first()
        if not receiver:
            raise HTTPException(status_code=404, detail="Recipient not found")
        if sender.upi_id == receiver.upi_id:
            raise HTTPException(status_code=400, detail="Cannot send to self")
        if sender.balance < req.amount:
            raise HTTPException(status_code=400, detail="Insufficient balance")
        sender.balance -= req.amount
        receiver.balance += req.amount
        txn = models.Transaction(sender_id=sender.id, receiver_upi=receiver.upi_id, amount=req.amount)
        db.add(txn)
        db.commit()
        return {"message": f"₹{req.amount} sent to {receiver.upi_id}"}
    except HTTPException:
        raise
    except Exception:
        db.rollback()
        logger.exception("Transaction failed")
        raise HTTPException(status_code=500, detail="Transaction failed")

@app.get("/me/transactions", response_model=List[schemas.TransactionOut])
def my_transactions(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    txns = db.query(models.Transaction).options(joinedload(models.Transaction.sender)).filter(
        (models.Transaction.sender_id == current_user.id) | (models.Transaction.receiver_upi == current_user.upi_id)
    ).order_by(models.Transaction.created_at.desc()).all()
    return [
        schemas.TransactionOut(
            sender_upi=t.sender.upi_id if t.sender else None,
            receiver_upi=t.receiver_upi,
            amount=t.amount,
            created_at=t.created_at
        ) for t in txns
    ]