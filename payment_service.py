import uuid
import os
import aiohttp
import base64
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models import User, Payment

STORE_ID = os.getenv("STORE_ID")
SECRET_KEY = os.getenv("SECRET_KEY")
RETURN_URL = os.getenv("RETURN_URL")
API_URL = os.getenv("API_URL")
api_url = "https://api.yookassa.ru/v3/payments"

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
        return user

    @classmethod
    async def firstPayment(cls, session: AsyncSession, telegramId: int, amount: int) -> str:
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
                "return_url": RETURN_URL  
            },
            "capture": True,
            "description": f"Пользователь ID: {telegramId} зарегистрирован",
            "save_payment_method": True
        }

        auth_string = f"{STORE_ID}:{SECRET_KEY}"
        # print(f"kus12 auth_string: {auth_string}")
        auth_bytes = auth_string.encode("utf-8")
        # print(f"kus13 auth_bytes: {auth_bytes}")
        base64_auth = base64.b64encode(auth_bytes).decode("utf-8")
        # print(f"kus14 base64_auth: {base64_auth}")
        headers = {
            "Idempotence-Key": idempotence_key,
            "Content-Type": "application/json",
            "Authorization": f"Basic {base64_auth}"
        }

        async with aiohttp.ClientSession(headers=headers) as client:
            async with client.post(api_url, json=payload, timeout=15.0) as response:
                print(f"kus15 response.status: {response.status}")
                print(f"kus16 response.text: {await response.text()}")
                if response.status != 200:
                    response_text = await response.text()
                    raise Exception(f"kus11 ЮKassa API error {response.status}: {response_text}")
                
                yoo_payment_data = await response.json()

        new_payment = Payment(
            yoo_payment_id=yoo_payment_data.get("id"),
            user_id=user.id,
            amount=amount,
            status="pending",
            created_at=datetime.utcnow()
        )
        session.add(new_payment)
        await session.commit()

        confirmation_url = yoo_payment_data.get("confirmation", {}).get("confirmation_url")
        return confirmation_url
