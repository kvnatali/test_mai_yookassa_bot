import asyncio
from database import async_session_maker
from payment_service import PaymentService

async def main():

    TEST_TELEGRAM_ID = 999999999 
    PAYMENT_AMOUNT = 500 

    print("Подключение к БД")
    async with async_session_maker() as session:
        try:
            print(f"TEST_TELEGRAM_ID:{TEST_TELEGRAM_ID}, PAYMENT_AMOUNT {PAYMENT_AMOUNT}")
            
            confirmation_url = await PaymentService.firstPayment(
                session=session, 
                telegramId=TEST_TELEGRAM_ID, 
                amount=PAYMENT_AMOUNT
            )
            
            print("Ok")
            print(f"confirmation_url: {confirmation_url}")
            
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
