from fastapi import FastAPI

from app.routers.user import router as user_router
from app.routers.wallet import router as wallet_router
from app.routers.transaction import router as transaction_router
from app.routers.deposit import router as deposit_router
from app.routers.transfer import router as transfer_router
from app.routers.withdrawal import router as withdrawal_router
from app.routers.admin import router as admin_router
from app.routers.refund import router as refund_router 
from app.routers.notification import router as notification_router
from app.routers.dashboard import router as dashboard_router
from app.routers.audit_log import router as audit_log_router
from contextlib import asynccontextmanager

from app.tasks.scheduled_jobs import (
    start_scheduler,
    scheduler,
)
@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()

    try:
        yield
    finally:
        if scheduler.running:
            scheduler.shutdown(wait=False)
            
app = FastAPI(
    title="Digital Wallet & Transaction Processing Platform",
    version="1.0.0",
    description="Backend API for secure digital wallet and transaction processing.",
    lifespan=lifespan,
)

app.include_router(user_router)
app.include_router(wallet_router)
app.include_router(transaction_router)
app.include_router(deposit_router)
app.include_router(transfer_router)
app.include_router(withdrawal_router)
app.include_router(admin_router)
app.include_router(refund_router)
app.include_router(notification_router)
app.include_router(dashboard_router)
app.include_router(audit_log_router)


@app.get("/")
def root():
    return {
        "message": "Digital Wallet Platform API is running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }