from fastapi import FastAPI
from app import models
from app.database import engine
from app.routers import transaction

app = FastAPI()

models.Base.metadata.create_all(bind=engine)

app.include_router(transaction.router)
