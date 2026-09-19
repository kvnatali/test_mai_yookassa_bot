import asyncio
from scheduler import checkAndRunRecurrentPayments
from database import async_session_maker
from models import Payment
from sqlalchemy import update

async def force_fail_trigger():
    print("неудачная подписка")
    async with async_session_maker() as session:

        from datetime import datetime
        await session.execute(
            update(Payment)
            .where(Payment.status == "succeeded")
            .values(status="canceled", retry_at=datetime.utcnow(), attempts=0)
        )
        await session.commit()
    
    print("планировщик списаний, запуск")
    await checkAndRunRecurrentPayments()
    print("Проверка завершена.")

if __name__ == "__main__":
    asyncio.run(force_fail_trigger())
