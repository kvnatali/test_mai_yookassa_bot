import os
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from database import get_db
from models import Payment, User
from scheduler import checkAndRunRecurrentPayments, handlePaymentFailure
from notifications import sendPaymentNotification 

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = AsyncIOScheduler()
    scheduler.add_job(checkAndRunRecurrentPayments, 'interval', hours=1)
    scheduler.start()
    print("планировщик запущен")
    yield
    scheduler.shutdown()
    print("планировщик остановлен")

app = FastAPI(title="YooKassa Billing System", lifespan=lifespan)

@app.middleware("http")
async def addNgrokSkipHeader(request: Request, call_next):
    response: Response = await call_next(request)
    response.headers["ngrok-skip-browser-warning"] = "true"
    return response

@app.post("/webhook/yookassa")
async def yookassaWebhook(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        event_data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    event_type = event_data.get("event")
    object_data = event_data.get("object", {})
    yoo_payment_id = object_data.get("id")

    if not yoo_payment_id:
        return {"status": "ignored", "reason": "No payment ID"}

    result = await db.execute(select(Payment).where(Payment.yoo_payment_id == yoo_payment_id))
    payment = result.scalar_one_or_none()

    if not payment:
        return {"status": "ignored", "reason": "Payment not found in DB"}

    result_user = await db.execute(select(User).where(User.id == payment.user_id))
    user = result_user.scalar_one()

    if event_type == "payment.succeeded":
        payment.status = "succeeded"
        payment.retry_at = None
        
        payment_method = object_data.get("payment_method", {})
        payment_method_id = payment_method.get("id")
        
        if payment_method_id and payment_method.get("saved") is True:
            user.payment_method_id = payment_method_id
            
        user.is_active = True
        await db.commit()

        await sendPaymentNotification(
            status="success",
            amount=str(payment.amount),
            userId=str(user.telegram_id)
        )
        return {"status": "ok"}

    elif event_type == "payment.canceled":
        cancellation_details = object_data.get("cancellation_details", {})
        reason = cancellation_details.get("reason", "unknown")
        
        await handlePaymentFailure(db, user, payment, reason)
        return {"status": "ok"}

    return {"status": "ignored", "reason": "Unhandled event type"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
