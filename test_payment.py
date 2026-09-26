import uuid
import pytest
import pytest_asyncio
import logging
from yookassa import Configuration, Payment as YooPayment
from config import settings
from database import async_session_maker
from payment_service import PaymentService
from time_service import TimeService, MockTimeService

logger = logging.getLogger(__name__)

Configuration.account_id = settings.YOOKASSA_SHOP_ID
Configuration.secret_key = settings.YOOKASSA_SECRET_KEY

def test_yookassa_connection():
    logger.info(f"Тест подключения, Shop ID: {Configuration.account_id}")
    
    secret_preview = Configuration.account_id[:8] if Configuration.secret_key else "None"
    logger.info(f"Secret Key: {secret_preview}... (скрыт)")
    
    idempotence_key = str(uuid.uuid4())
    
    try:
        payment = YooPayment.create({
            "amount": {
                "value": "150.00",
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": settings.RETURN_URL
            },
            "capture": True,
            "description": "Тестовое соединение"
        }, idempotence_key)
        
        logger.info("успешно Ok")
        
        assert payment.id is not None, "ЮKassa не вернула ID платежа"
        assert payment.status == "pending", f"Ожидался статус pending, получен: {payment.status}"
        assert payment.confirmation.confirmation_url.startswith("https://"), "Некорректная ссылка на оплату"
        
        logger.info(f"payment.id: {payment.id}, Ссылка: {payment.confirmation.confirmation_url}")

    except Exception as e:
        logger.error(f"Ошибка подключения к ЮKassa API: {e}", exc_info=True)
        raise e

@pytest_asyncio.fixture(loop_scope="session")
async def db_session():
    async with async_session_maker() as session:
        yield session
        await session.rollback() 

@pytest.mark.asyncio(loop_scope="session")
@pytest.mark.parametrize(
    "time_service_instance",
    [
        TimeService(),
        MockTimeService()
    ],
    ids=["real_time", "mock_time"]
)
async def test_first_payment_success(db_session, time_service_instance):
    TEST_TELEGRAM_ID = 999999999
    PAYMENT_AMOUNT = 600

    logger.info(f"Старт теста: [{time_service_instance.__class__.__name__}]")
    
    confirmation_url = await PaymentService.firstPayment(
        session=db_session, 
        telegramId=TEST_TELEGRAM_ID, 
        amount=PAYMENT_AMOUNT,
        time_service=time_service_instance
    )

    assert confirmation_url is not None, "нет ссылки для подтверждения платежа"
    assert confirmation_url.startswith("https://"), f"Некорректный формат URL: {confirmation_url}"
    
    logger.info(f"Успех, получен confirmation_url")
