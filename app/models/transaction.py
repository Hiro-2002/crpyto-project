from app.database import Base
from sqlalchemy import DECIMAL, Computed, String, Float, DateTime, Integer, Column


class Transaction(Base):
    __tablename__ = 'transactions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_type = Column(String(10), nullable=False)
    currency = Column(String(10), nullable=False)
    quantity = Column(DECIMAL(18, 8), nullable=False)
    price_at_time = Column(DECIMAL(18, 8), nullable=False)
    total_value = Column(DECIMAL(18, 8), Computed('quantity * price_at_time'))
    created_at = Column(DateTime, nullable=False)