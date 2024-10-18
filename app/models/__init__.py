from sqlalchemy.ext.declarative import declarative_base

# Create the base class for your models
Base = declarative_base()

# Import your models so they are registered with Base.metadata
from app.models.transaction import Transaction  # or any other models you may have
