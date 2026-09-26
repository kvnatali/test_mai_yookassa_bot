import logging
from aiogram import Bot
from config import settings 

logger = logging.getLogger(__name__)

async def sendPaymentNotification(status: str, amount: str, userId: str, reason: str = None):
    token = settings.TG_BOT_TOKEN
    chat_id = settings.TG_CHAT_ID

    friendly_reason = reason
    if reason == "insufficient_funds":
        friendly_reason = "Недостаточно денег"
    elif reason == "card_expired_or_invalid":
        friendly_reason = "Карта истекла"
    elif reason == "permission_denied":
        friendly_reason = "Операция отклонена"

    if status == "success":
        text = (
            f"Успешный платеж. userId: `{userId}`,  amount: {amount}"
        )
    else:
        text = (
            f"Ошибка {friendly_reason or 'unknown'}. userId: `{userId}`,  amount: {amount}"
        )

    try:
        async with Bot(token=token) as bot:
            await bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Ошибка: {e}", exc_info=True)
