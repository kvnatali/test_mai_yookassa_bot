import os
from aiogram import Bot
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TG_BOT_TOKEN")
CHAT_ID = os.getenv("TG_CHAT_ID")

async def sendPaymentNotification(status: str, amount: str, userId: str, reason: str = None):
    if not TOKEN or not CHAT_ID:
        print(f"TOKEN or CHAT_ID error Status={status}, Amount={amount}, User={userId}, Reason={reason}")
        return

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
        async with Bot(token=TOKEN) as bot:
            await bot.send_message(chat_id=CHAT_ID, text=text, parse_mode="Markdown")
    except Exception as e:
        print(f"Ошибка уведомления в Telegram: {e}")
