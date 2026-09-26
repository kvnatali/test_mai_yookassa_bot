import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import async_session_maker
from payment_service import PaymentService
from config import settings

logger = logging.getLogger(__name__)

SUBSCRIPTION_PRICE = 550  

bot = Bot(token=settings.TG_BOT_TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def commandStartHandler(message: types.Message):
    telegram_id = message.from_user.id
    
    async with async_session_maker() as db_session:
        try:
            logger.info(f"Старт обработки команды /start для пользователя {telegram_id}")
            
            confirmation_url = await PaymentService.firstPayment(
                session=db_session,
                telegramId=telegram_id,
                amount=SUBSCRIPTION_PRICE
            )
            
            logger.info(f"Ссылка успешно создана. confirmation_url: {confirmation_url}")
            
            builder = InlineKeyboardBuilder()
            builder.button(
                text=f"Оплатить {SUBSCRIPTION_PRICE} ₽", 
                url=confirmation_url
            )
            
            text = (
                f"Привет, {message.from_user.first_name}!\n\n"
                f"Сейчас спишется {SUBSCRIPTION_PRICE} ₽ для регистрации подписки."
            )
            
            await message.answer(text=text, reply_markup=builder.as_markup())
            
        except Exception as e:
            logger.error(f"Ошибка при создании платежа для пользователя {telegram_id}: {e}", exc_info=True)
            await message.answer("Не получилось создать ссылку для оплаты. Попробуйте позже.")

async def startBot():
    logger.info("Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(startBot())
