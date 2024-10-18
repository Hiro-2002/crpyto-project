from app.database import Base
from sqlalchemy import String, Float, DateTime, Integer, Column


class Transaction(Base):
    __tablename__ = 'transactions'

    id = Column(Integer, primary_key=True, index=True)
    transaction_type = Column(String)
    currency = Column(String)
    quantity = Column(Float)
    price_at_time = Column(Float)
    total_value = Column(Float)
    created_at = Column(DateTime)