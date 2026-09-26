import asyncio
import logging
from sqlalchemy import update
from database import async_session_maker
from models import Payment
from scheduler import checkAndRunRecurrentPayments
from time_service import TimeService
from config import settings

logger = logging.getLogger(__name__)

async def force_fail_trigger():
    logger.info("неудачная подписка")
    
    time_service = TimeService()
    current_time = time_service.get_current_time()

    async with async_session_maker() as session:
        await session.execute(
            update(Payment)
            .where(Payment.status == "succeeded")
            .values(
                status="canceled", 
                retry_at=current_time, 
                attempts=0
            )
        )
        await session.commit()
    
    logger.info("планировщик списаний, запуск")
    await checkAndRunRecurrentPayments()
    logger.info("Проверка завершена.")

if __name__ == "__main__":
    asyncio.run(force_fail_trigger())

