import logging
from dotenv import load_dotenv
import os
import smtplib
from email.mime.text import MIMEText
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from email_validator import validate_email, EmailNotValidError

# Загрузка переменных из .env
load_dotenv()
TELEGRAM_API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")
SMTP_SERVER = "smtp.yandex.ru"
SMTP_PORT = 587
SMTP_LOGIN = os.getenv("SMTP_LOGIN")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

# Логирование
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
bot = Bot(token=TELEGRAM_API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Состояния
class Form(StatesGroup):
    email = State()
    message = State()

# Стартовое сообщение
@dp.message(Command("start"))
async def start(message: Message, state: FSMContext):
    await message.answer("Привет! Введите ваш email:")
    await state.set_state(Form.email)

# Проверка email
@dp.message(Form.email)
async def get_email(message: Message, state: FSMContext):
    try:
        email = message.text
        validate_email(email)
        await state.update_data(email=email)
        await message.answer("Email принят. Теперь введите текст сообщения:")
        await state.set_state(Form.message)
    except EmailNotValidError as e:
        await message.answer(f"Некорректный email. Попробуйте снова. Ошибка: {e}")

# Получение текста сообщения и отправка письма
@dp.message(Form.message)
async def get_message(message: Message, state: FSMContext):
    data = await state.get_data()
    email = data.get("email")
    text = message.text

    try:
        send_email(email, text)
        await message.answer("Сообщение успешно отправлено!")
    except Exception as e:
        await message.answer(f"Ошибка при отправке сообщения: {e}")
    finally:
        await state.clear()

# Функция отправки email
def send_email(recipient_email, text):
    try:
        msg = MIMEText(text, "plain", "utf-8")
        msg["Subject"] = "Сообщение от Telegram-бота"
        msg["From"] = SMTP_LOGIN
        msg["To"] = recipient_email

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            try:
                server.login(SMTP_LOGIN, SMTP_PASSWORD)
            except smtplib.SMTPAuthenticationError:
                raise Exception("Ошибка аутентификации. Проверьте логин или пароль.")
            except smtplib.SMTPConnectError:
                raise Exception("Не удалось подключиться к SMTP-серверу. Проверьте сервер или интернет-соединение.")

            server.sendmail(SMTP_LOGIN, recipient_email, msg.as_string())
            logging.info(f"Письмо успешно отправлено на {recipient_email} с текстом: {text}")
    except smtplib.SMTPException as e:
        logging.error(f"Ошибка при отправке сообщения: {e}")
        raise Exception("Ошибка SMTP. Проверьте настройки или соединение.")
    except Exception as e:
        logging.error(f"Общая ошибка: {e}")
        raise Exception(f"Общая ошибка: {e}")

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
