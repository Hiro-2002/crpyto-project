from collections import defaultdict, deque
from typing import Annotated
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from decimal import Decimal
from fastapi import APIRouter, Depends, status
from app.services.price_fetcher import fetch_latest_price
from app.models.transaction import Transaction
from app.database import SessionLocal
from app.schemas.transaction import TransactionRequest
from fastapi.responses import FileResponse, HTMLResponse

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

@router.get("/", response_class=HTMLResponse)
async def read_root():
    return FileResponse("client/index.html")

# Create a new transaction
@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_transaction(db: db_dependency, transaction_request: TransactionRequest):
    latest_price = await fetch_latest_price(transaction_request.currency)
    created_at = transaction_request.created_at or datetime.now(tz=timezone.utc)

    transaction_model = Transaction(
        transaction_type=transaction_request.transaction_type.upper(),
        currency=transaction_request.currency.upper(),
        quantity=float(transaction_request.quantity),
        price_at_time=latest_price,  
        created_at=created_at
    )

    db.add(transaction_model)
    db.commit()
    db.refresh(transaction_model)

    return transaction_model


# HTML
@router.get("/get", response_class=HTMLResponse)
async def get_transactions(db: db_dependency):
    transactions = db.query(Transaction).order_by(Transaction.created_at).all()
    html_content = "<tbody>"
    
    for transaction in transactions:
        created_at = datetime.fromisoformat(transaction.created_at.isoformat()).strftime("%Y-%m-%d %H:%M:%S")
        html_content += f"""
        <tr>
            <td>{transaction.transaction_type}</td>
            <td>{transaction.id}</td>
            <td>{transaction.total_value:.2f}</td>
            <td>{transaction.quantity}</td>
            <td>{transaction.price_at_time:.2f}</td>
            <td>{transaction.currency}</td>
            <td>{created_at}</td>
        </tr>
        """
    
    html_content += "</tbody>"
    return HTMLResponse(content=html_content)



# Profit/loss by currency
@router.get("/profit-loss/currency", status_code=status.HTTP_200_OK)
async def get_currency_profit_loss(db: db_dependency):
    transactions = db.query(Transaction).order_by(Transaction.created_at).all()

    if not transactions:
        return {"message": "No transactions found", "profit_loss": []}

    holdings = defaultdict(deque)
    currency_profit_loss = defaultdict(Decimal)

    for transaction in transactions:
        if transaction.transaction_type == 'BUY':
            holdings[transaction.currency].append((transaction.quantity, transaction.price_at_time))
        elif transaction.transaction_type == 'SELL':
            if not holdings[transaction.currency]:
                return {"message": f"Cannot sell {transaction.currency}, no quantity left."}
                
            sell_quantity = transaction.quantity
            sell_price = transaction.price_at_time

            while sell_quantity > 0 and holdings[transaction.currency]:
                buy_quantity, buy_price = holdings[transaction.currency][0]

                if buy_quantity <= sell_quantity:
                    profit_or_loss = (sell_price - buy_price) * buy_quantity
                    currency_profit_loss[transaction.currency] += profit_or_loss
                    sell_quantity -= buy_quantity
                    holdings[transaction.currency].popleft()
                else:
                    profit_or_loss = (sell_price - buy_price) * sell_quantity
                    currency_profit_loss[transaction.currency] += profit_or_loss
                    holdings[transaction.currency][0] = (buy_quantity - sell_quantity, buy_price)
                    sell_quantity = 0

    currency_profit_loss_list = [
        {"currency": currency, "profit_or_loss": float(profit_or_loss)}
        for currency, profit_or_loss in currency_profit_loss.items()
    ]

    return {"currency_profit_loss": currency_profit_loss_list}



# Total profit/loss
@router.get("/profit-loss/total", status_code=status.HTTP_200_OK)
async def get_total_profit_loss(db: db_dependency):
    transactions = db.query(Transaction).order_by(Transaction.created_at).all()

    if not transactions:
        return {"message": "No transactions found", "total_profit_loss": 0}

    holdings = defaultdict(deque)
    total_profit_loss = Decimal(0)

    for transaction in transactions:
        if transaction.transaction_type == 'BUY':
            holdings[transaction.currency].append((transaction.quantity, transaction.price_at_time))
        elif transaction.transaction_type == 'SELL':
            if not holdings[transaction.currency]:
                return {"message": f"Cannot sell {transaction.currency}, no quantity left."}
                
            sell_quantity = transaction.quantity
            sell_price = transaction.price_at_time

            while sell_quantity > 0 and holdings[transaction.currency]:
                buy_quantity, buy_price = holdings[transaction.currency][0]

                if buy_quantity <= sell_quantity:
                    profit_or_loss = (sell_price - buy_price) * buy_quantity
                    total_profit_loss += profit_or_loss
                    sell_quantity -= buy_quantity
                    holdings[transaction.currency].popleft()
                else:
                    profit_or_loss = (sell_price - buy_price) * sell_quantity
                    total_profit_loss += profit_or_loss
                    holdings[transaction.currency][0] = (buy_quantity - sell_quantity, buy_price)
                    sell_quantity = 0

    return {"total_profit_loss": float(total_profit_loss)}



# Daily profit/loss
@router.get("/profit-loss/daily", status_code=status.HTTP_200_OK)
async def get_daily_profit_loss(db: db_dependency):
    transactions = db.query(Transaction).order_by(Transaction.created_at).all()

    if not transactions:
        return {"message": "No transactions found", "daily_profit_loss": []}

    holdings = defaultdict(deque)
    daily_profit_loss = defaultdict(Decimal)

    for transaction in transactions:
        transaction_date = transaction.created_at.date()

        if transaction.transaction_type == 'BUY':
            holdings[transaction.currency].append((transaction.quantity, transaction.price_at_time))
        elif transaction.transaction_type == 'SELL':
            if not holdings[transaction.currency]:
                return {"message": f"Cannot sell {transaction.currency}, no quantity left."}
                
            sell_quantity = transaction.quantity
            sell_price = transaction.price_at_time

            while sell_quantity > 0 and holdings[transaction.currency]:
                buy_quantity, buy_price = holdings[transaction.currency][0]

                if buy_quantity <= sell_quantity:
                    profit_or_loss = (sell_price - buy_price) * buy_quantity
                    daily_profit_loss[transaction_date] += profit_or_loss
                    sell_quantity -= buy_quantity
                    holdings[transaction.currency].popleft()
                else:
                    profit_or_loss = (sell_price - buy_price) * sell_quantity
                    daily_profit_loss[transaction_date] += profit_or_loss
                    holdings[transaction.currency][0] = (buy_quantity - sell_quantity, buy_price)
                    sell_quantity = 0

    daily_profit_loss_list = [
        {"date": str(transaction_date), "profit_or_loss": float(profit_or_loss)}
        for transaction_date, profit_or_loss in sorted(daily_profit_loss.items())
    ]

    return {"daily_profit_loss": daily_profit_loss_list}
