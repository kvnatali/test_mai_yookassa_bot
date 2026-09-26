import uuid
import logging
import aiohttp
import base64
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models import User, Payment
from config import settings
from time_service import TimeService

logger = logging.getLogger(__name__)

class PaymentService:
    @staticmethod
    async def getOrCreateUser(session: AsyncSession, telegramId: int) -> User:
        result = await session.execute(select(User).where(User.telegram_id == telegramId))
        user = result.scalar_one_or_none()
        
        if not user:
            user = User(telegram_id=telegramId, is_active=False)
            session.add(user)
            await session.commit()
            await session.refresh(user)
            logger.info(f"Создан новый пользователь: {telegramId}")
        return user

    @classmethod
    async def firstPayment(
        cls, 
        session: AsyncSession, 
        telegramId: int, 
        amount: int, 
        time_service: TimeService = TimeService()
    ) -> str:
        user = await cls.getOrCreateUser(session, telegramId)
        idempotence_key = str(uuid.uuid4())

        payload = {
            "amount": {
                "value": f"{amount}.00",
                "currency": "RUB"
            },
            "payment_method_data": {
                "type": "bank_card"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": settings.RETURN_URL
            },
            "capture": True,
            "description": f"Пользователь ID: {telegramId} зарегистрирован",
            "save_payment_method": True
        }

        auth_string = f"{settings.YOOKASSA_SHOP_ID}:{settings.YOOKASSA_SECRET_KEY}"
        auth_bytes = auth_string.encode("utf-8")
        base64_auth = base64.b64encode(auth_bytes).decode("utf-8")
        
        headers = {
            "Idempotence-Key": idempotence_key,
            "Content-Type": "application/json",
            "Authorization": f"Basic {base64_auth}"
        }

        target_url = f"{settings.API_URL}/payments"

        async with aiohttp.ClientSession(headers=headers) as client:
            async with client.post(target_url, json=payload, timeout=15.0) as response:
                response_text = await response.text()
                logger.info(f"kus15 response.status: {response.status} response.text: {response_text}")
                
                if response.status != 200:
                    logger.error(f"Ошибка API ЮKassa {response.status}: {response_text}")
                    raise Exception(f"kus11 ЮKassa API error {response.status}: {response_text}")
                
                yoo_payment_data = await response.json()

        new_payment = Payment(
            yoo_payment_id=yoo_payment_data.get("id"),
            user_id=user.id,
            amount=amount,
            status="pending",
            created_at=time_service.get_current_time()
        )
        session.add(new_payment)
        await session.commit()
        logger.info(f"Платеж {new_payment.yoo_payment_id} успешно сохранен в БД для пользователя {telegramId}")

        confirmation_url = yoo_payment_data.get("confirmation", {}).get("confirmation_url")
        return confirmation_url
