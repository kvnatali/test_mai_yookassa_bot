import uuid
from datetime import datetime, timedelta
from sqlalchemy import select
from yookassa import Payment as YooPayment

from database import async_session_maker
from models import User, Payment
from notifications import sendPaymentNotification

MAX_RETRY_ATTEMPTS = 3
SUBSCRIPTION_PRICE = 500

async def checkAndRunRecurrentPayments():
    async with async_session_maker() as session:
        now = datetime.utcnow()
        
        failed_query = select(Payment).where(
            Payment.status == "canceled",
            Payment.retry_at <= now,
            Payment.attempts < MAX_RETRY_ATTEMPTS
        )
        failed_payments = (await session.execute(failed_query)).scalars().all()
        
        for failed_pay in failed_payments:
            result_user = await session.execute(select(User).where(User.id == failed_pay.user_id))
            user = result_user.scalar_one()
            
            if user.payment_method_id:
                await executeRecurrentCharge(session, user, failed_pay)

async def executeRecurrentCharge(session, user: User, old_payment: Payment):
    idempotence_key = str(uuid.uuid4())
    
    try:
        yoo_payment_data = YooPayment.create({
            "amount": {
                "value": f"{SUBSCRIPTION_PRICE}.00",
                "currency": "RUB"
            },
            "capture": True,
            "payment_method_id": user.payment_method_id,
            "description": f"Cписание подписки. telegram_id: {user.telegram_id}"
        }, idempotence_key)
        
        new_payment = Payment(
            yoo_payment_id=yoo_payment_data.id,
            user_id=user.id,
            amount=SUBSCRIPTION_PRICE,
            status="pending",
            attempts=old_payment.attempts
        )
        
        old_payment.status = "retried" 
        session.add(new_payment)
        await session.commit()
        
    except Exception as e:
        await handlePaymentFailure(session, user, old_payment, reason="api_error")

async def handlePaymentFailure(session, user: User, payment: Payment, reason: str):
    payment.attempts += 1
    payment.fail_reason = reason
    
    if payment.attempts < MAX_RETRY_ATTEMPTS:
        payment.retry_at = datetime.utcnow() + timedelta(days=1)
        payment.status = "canceled"
        
        await sendPaymentNotification(
            status="fail",
            amount=str(payment.amount),
            userId=str(user.telegram_id),
            reason=f"{reason} (attempt: {payment.attempts} из {MAX_RETRY_ATTEMPTS}.)"
        )
    else:
        payment.status = "failed_final"
        payment.retry_at = None
        user.is_active = False
        
        await sendPaymentNotification(
            status="fail",
            amount=str(payment.amount),
            userId=str(user.telegram_id),
            reason=f"MAX_RETRY_ATTEMPTS: ({MAX_RETRY_ATTEMPTS}) finished, status=fail"
        )
        
    await session.commit()
