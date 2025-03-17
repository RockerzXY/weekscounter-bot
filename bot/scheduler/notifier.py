from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
import asyncio
import random
from .misc import phrases


def generate_notification_text(user_info):
    """Генерация текста уведомления"""
    custom_name = user_info['custom_name']
    birthdate = datetime.strptime(user_info['birthdate'], "%Y-%m-%d").date()
    today = datetime.now().date()
    
    delta = today - birthdate
    
    weeks_lived = delta.days // 7
    total_weeks = 4000

    # Выбор случайной фразы
    random_phrase = random.choice(phrases)

    return f"<b>{custom_name}</b>, сегодня ты прожил(а) свою <b>{weeks_lived}</b> неделю из <b>{total_weeks}</b>.\n<i>{random_phrase}</i>"


class Notifier:
    def __init__(self, bot, db, logger, scheduler: AsyncIOScheduler):
        self.bot = bot
        self.db = db
        self.logger = logger
        self.scheduler = scheduler

    async def start(self):
        """Запуск планировщика уведомлений"""
        if not self.scheduler.running:
            self.scheduler.start()
            self.logger.info("Планировщик уведомлений запущен.")
            await asyncio.sleep(0.1)
        await self.schedule_notifications()

    async def send_notification(self, user_id):
        """Отправка уведомления пользователю"""
        user_info = self.db.get_user_info(user_id)

        if not user_info:
            self.logger.warning(f"Пользователь {user_id} не найден в базе данных.")
            return
        message_text = generate_notification_text(user_info)

        try:
            await self.bot.send_message(user_id, message_text, parse_mode='HTML')
            self.db.update_last_notification(user_id, datetime.now().date())
            self.logger.info(f"Уведомление отправлено пользователю {user_id}.")
            
        except Exception as e:
            self.logger.error(f"Ошибка при отправке уведомления пользователю {user_id}: {e}")

    async def update_user_notification(self, user_id):
        """Обновление задачи уведомления для пользователя"""
        if not self.scheduler.running:
            self.logger.critical("Планировщик не запущен! Задачи обновлены не будут.")
            return

        # Удаляем старую задачу (если есть)
        for job in self.scheduler.get_jobs():
            if job.args and job.args[0] == user_id:
                job.remove()
                self.logger.info(f"Старая задача уведомления для пользователя {user_id} удалена.")

        # Получаем данные пользователя
        user_info = self.db.get_user_info(user_id)
        if not user_info:
            self.logger.warning(f"Данные пользователя {user_id} не найдены.")
            return

        # Получаем день недели и время уведомления
        notify_day = user_info['notify_day']
        notify_time = user_info['notify_time']

        # Преобразуем день недели в формат, понятный для cron
        days_map = {
            "Пн": "mon", 
            "Вт": "tue",
            "Ср": "wed",
            "Чт": "thu",
            "Пт": "fri",
            "Сб": "sat",
            "Вс": "sun"
        }
        day_of_week = days_map.get(notify_day, "mon")  # По-умолчанию понедельник

        # Преобразуем время уведомления в объект времени
        notify_time_obj = datetime.strptime(notify_time, "%H:%M").time()


        ## Планируем новую задачу
        self.scheduler.add_job(
            self.send_notification,
            'cron',
            day_of_week=day_of_week,
            hour=notify_time_obj.hour,
            minute=notify_time_obj.minute,
            args=[user_id]
        )
        
        ## Для дебагинга планировщика уведомлений
        # self.scheduler.add_job(
        #     self.send_notification,
        #     'interval',
        #     minutes=1,
        #     args=[user_id]
        # )

        self.logger.info(f"Новая задача уведомления для пользователя {user_id} запланирована.")

    async def schedule_notifications(self):
        """Планирование уведомлений для всех пользователей"""
        users = self.db.get_all_users()

        if not users:
            self.logger.warning("Нет пользователей для планирования уведомлений.")
            return
        
        for user_id in users:
            await self.update_user_notification(user_id)
        
        self.logger.info(f"Уведомления запланированы для {len(users)} пользователей.")
