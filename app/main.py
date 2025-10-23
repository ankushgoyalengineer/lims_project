from fastapi import FastAPI
from app.db import engine, Base
from app.core.config import ENV
import logging

app = FastAPI(title="LIMS Backend")

@app.on_event("startup")
def startup():
    if ENV == "development":
        Base.metadata.create_all(bind=engine)
        logging.info("Created tables (development).")

@app.get("/health")
def health_check():
    return {"status": "ok"}
