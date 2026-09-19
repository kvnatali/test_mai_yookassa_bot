import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.client.session.aiohttp import AiohttpSession
# from aiohttp_proxy import ProxyConnector
from dotenv import load_dotenv

from database import async_session_maker
from payment_service import PaymentService
from aiohttp_socks import ProxyConnector 

load_dotenv()

TOKEN = os.getenv("TG_BOT_TOKEN")
SUBSCRIPTION_PRICE = 500  

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def commandStartHandler(message: types.Message):
    telegram_id = message.from_user.id
    
    async with async_session_maker() as db_session:
        try:
            print("kus1")
            confirmation_url = await PaymentService.firstPayment(
                session=db_session,
                telegramId=telegram_id,
                amount=SUBSCRIPTION_PRICE
            )
            print(f"kus2 confirmation_url: {confirmation_url}")
            builder = InlineKeyboardBuilder()
            builder.button(
                text=f"Оплатить {SUBSCRIPTION_PRICE} ₽", 
                url=confirmation_url
            )
            
            text = (
                f"Привет, {message.from_user.first_name}!\n\n"
                f"Сейчас спишется {SUBSCRIPTION_PRICE} "
            )
            
            await message.answer(text=text, reply_markup=builder.as_markup())
            
        except Exception as e:
            print(f"Ошибка у пользователя {telegram_id}: {e}")
            await message.answer("Не получилось создать ссылку для оплаты")

async def startBot():
    print("Бот работает")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(startBot())
