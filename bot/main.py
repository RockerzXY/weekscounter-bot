from core import executor, dp, logger, notifier


# Запуск планировщика уведомления (после бота)
async def on_startup(_):
    try:
        await notifier.start()
    except Exception as e:
        logger.error(f"Ошибка при запуске планировщика: {e}")
        raise


# Запуск бота
if __name__ == '__main__':
    from handlers import dp
    try:
        logger.info("Бот запущен.")
        executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        raise