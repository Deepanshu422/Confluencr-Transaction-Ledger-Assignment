from fastapi import FastAPI
from app.database import engine, Base
import app.models  
from app.routers import account_router, transfer_router
from app.exceptions import LedgerException, ledger_exception_handler
from app.config import settings

# Create tables if they do not exist
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="High-integrity ledger system with row-level locking, ACID transactions, and idempotency guarantees.",
)

# Global custom error handler
app.add_exception_handler(LedgerException, ledger_exception_handler)

# Register endpoints
app.include_router(account_router)
app.include_router(transfer_router)


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy"}