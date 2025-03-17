import os
import logging
from logging.handlers import RotatingFileHandler
from aiogram import Bot, Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from db import Database
from scheduler.notifier import Notifier


# Настройка логирования
log_dir = os.path.join(os.getcwd(), "./logs/")
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

try:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            RotatingFileHandler(
                os.path.join(log_dir, "bot.log"),
                maxBytes=10 * 1024 * 1024,   # 10 MB
                backupCount=3                # Хранить 3 backup-файла
            ),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)
except Exception as e:
    print(f"Ошибка при инициализации логирования: {e}")
    raise

# Загрузка переменных окружения
TOKEN = os.getenv('TOKEN')
if not TOKEN:
    logger.critical("Токен бота не найден в переменных окружения! Проверьте переменную TOKEN.")
    raise ValueError("Токен бота не найден в переменных окружения!")

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Инициализация базы данных
db_path = os.path.join(os.getcwd(), "./db/database.db")
try:
    db = Database(db_path)
    logger.info(f"База данных успешно инициализирована.")
except Exception as e:
    logger.critical(f"Ошибка при инициализации базы данных: {e}")
    raise

# Инициализация планировщика
scheduler = AsyncIOScheduler()

# Инициализация планировщика уведомления
notifier = Notifier(bot, db, logger, scheduler)
