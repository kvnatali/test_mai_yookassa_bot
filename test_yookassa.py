import os
import uuid
from dotenv import load_dotenv
from yookassa import Configuration, Payment

load_dotenv()

Configuration.account_id = os.getenv("STORE_ID")
Configuration.secret_key = os.getenv("SECRET_KEY")

def test_connection():
    print("Проверка подключения")
    print(f"Shop ID: {Configuration.account_id}")
    print(f"Secret Key: {Configuration.secret_key[:8]}... (скрыт)")
    
    idempotence_key = str(uuid.uuid4())
    
    try:
        print("\nОтправка тестового запроса в ЮKassa (Sandbox)...")
        
        payment = Payment.create({
            "amount": {
                "value": "100.00",
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": os.getenv("RETURN_URL")
            },
            "capture": True,
            "description": "Тестовое соединение с ЮKassa API"
        }, idempotence_key)
        
        print("Ok")
        print(f"payment.id: {payment.id}, payment.status: {payment.status}")
        print(f"Ссылка на оплату: {payment.confirmation.confirmation_url}")

    except Exception as e:
        print("Ошибка подключения: {e}")

if __name__ == "__main__":
    test_connection()
