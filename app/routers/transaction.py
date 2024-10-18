from collections import defaultdict
import httpx
from typing import Annotated, Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Path, status
from app.models.transaction import Transaction
from app.database import SessionLocal



router = APIRouter()



def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


async def fetch_latest_price(currency: str) -> float:
    url = "https://api.nobitex.ir/market/stats"
    
    response = httpx.get(url=url)

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Failed to fetch market data")

    data = response.json()

    # Check available currencies in the response
    available_currencies = data["stats"].keys()  # Get the available currency pairs

    # Form the currency key
    currency_key = f"{currency.lower()}-usdt"

    # Check if the currency exists in the response
    if currency_key not in available_currencies:
        raise HTTPException(
            status_code=404, 
            detail=f"Currency not found. Available currencies are: {', '.join(available_currencies)}"
        )

    # Return the latest price
    return float(data["stats"][currency_key]["latest"])






class TransactionRequest(BaseModel):
    transaction_type: str = Field(max_length=3, min_length=3)
    currency: str = Field(min_length=3)
    quantity: float
    price_at_time: Optional[float] = None
    total_value: Optional[float] = None
    created_at: Optional[datetime] = None



# Create a new transaction
@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_transaction(
    db: db_dependency,
    transaction_request: TransactionRequest
):
    
    latest_price = await fetch_latest_price(transaction_request.currency)

    created_at = transaction_request.created_at or datetime.now(tz=timezone.utc)

    transaction_model = Transaction(
        transaction_type=transaction_request.transaction_type.upper(),
        currency=transaction_request.currency.upper(),
        quantity=float(transaction_request.quantity),
        price_at_time=latest_price,  
        total_value=transaction_request.quantity * latest_price, 
        created_at=created_at
    )

    db.add(transaction_model)
    db.commit()
    db.refresh(transaction_model)

    return transaction_model



# Get All Transactions
@router.get("/", status_code=status.HTTP_200_OK)
async def get_transactions(db: db_dependency):
    return db.query(Transaction).all()




@router.get("/profit-loss", status_code=status.HTTP_200_OK)
async def get_profit_loss(db: db_dependency):
    # Fetch all transactions
    transactions = db.query(Transaction).all()

    if not transactions:
        return {"message": "No transactions found", "profit_loss": []}

    currency_profit_loss = defaultdict(float)
    daily_profit_loss = defaultdict(float)
    total_profit_loss = 0.0

    for transaction in transactions:
        latest_price = await fetch_latest_price(transaction.currency)

        profit_or_loss = transaction.quantity * (latest_price - transaction.price_at_time)

        currency_profit_loss[transaction.currency] += profit_or_loss

        transaction_date = transaction.created_at.date()  # Get only the date part
        daily_profit_loss[transaction_date] += profit_or_loss

        total_profit_loss += profit_or_loss

    currency_profit_loss_list = [
        {"currency": currency, "profit_or_loss": profit_or_loss}
        for currency, profit_or_loss in currency_profit_loss.items()
    ]

    daily_profit_loss_list = [
        {"date": date.strftime("%Y-%m-%d"), "profit_or_loss": profit_or_loss}
        for date, profit_or_loss in daily_profit_loss.items()
    ]

    return {
        "currency_profit_loss": currency_profit_loss_list,
        "total_profit_loss": total_profit_loss,
        "daily_profit_loss": daily_profit_loss_list
    }
