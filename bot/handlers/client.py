from aiogram import types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.dispatcher import FSMContext
from datetime import datetime
import asyncio
from core import bot, dp, db, logger, notifier
from scheduler.notifier import generate_notification_text



class UserInit(StatesGroup):
    custom_name = State()       # Шаг 1: Запрос имени
    birthdate = State()         # Шаг 2: Запрос даты рождения
    notify_day = State()        # Шаг 3: Запрос дня недели для уведомлений
    notify_time = State()       # Шаг 4: Запрос времени для уведомлений


# Клавиатура для возвращения в FSM
def get_return_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(KeyboardButton("Назад"))
    return keyboard


# Клавиатура для выбора имени
def get_name_keyboard(username, full_name):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(KeyboardButton(username), KeyboardButton(full_name))
    keyboard.add(KeyboardButton("Назад"))
    return keyboard


# Клавиатура для выбора дня недели
def get_day_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.row("Пн", "Вт")
    keyboard.row("Ср", "Чт")
    keyboard.row("Пт", "Сб")
    keyboard.add("Вс")
    keyboard.add("Назад")
    return keyboard


# Клавиатура для выбора времени
def get_time_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    
    # Xасы по времени суток
    morning = [str(i) for i in range(6, 12)]   # Утро: 6-11
    day = [str(i) for i in range(12, 18)]      # День: 12-17
    evening = [str(i) for i in range(18, 24)]  # Вечер: 18-23
    night = [str(i) for i in range(0, 6)]      # Ночь: 0-5
    
    # Cтроки в клавиатуре
    keyboard.row(*morning[:3], *morning[3:])   # Утро: 6-8, 9-11
    keyboard.row(*day[:3], *day[3:])           # День: 12-14, 15-17
    keyboard.row(*evening[:3], *evening[3:])   # Вечер: 18-20, 21-23
    keyboard.row(*night[:3], *night[3:])       # Ночь: 0-2, 3-5
    
    # Добавляем кнопку "Назад"
    keyboard.add("Назад")
    
    return keyboard


# Команда /start
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    if db.user_exists(message.from_user.id):
        # Если пользователь уже зарегистрирован, выводим информацию
        user_info = db.get_user_info(message.from_user.id)
        msg += f"""
<b>{user_info['custom_name']}, ты когда-нибудь слышал о концепции 4000 недель?</b>
Эта идея гласит, средняя продолжительность жизни — около 70 лет, что составляет ~4000 недель.\n
Что ты почувствуешь, если узнаешь, на какой неделе ты <b>сейчас</b>?
<i>Прошёл ли ты уже половину?</i>\n\n
Ты указал датой рождения {user_info['birthdate']}, так?
Я буду каждую неделю напоминать тебе о чём-то важном в {user_info['notify_day']} {user_info['notify_time']}
"""
        await message.answer(msg, parse_mode='HTML')
        await message.answer(msg, parse_mode='HTML'
            f"Привет, {user_info['custom_name']}!\n"
            f"Твоя дата рождения: {user_info['birthdate']}\n"
            f"День уведомлений: {user_info['notify_day']}\n"
            f"Время уведомлений: {user_info['notify_time']}"
        )
        return

    # Если пользователь новый, начинаем процесс инициализации
    msg = f"""
<b>{message.from_user.username}, ты когда-нибудь слышал о концепции 4000 недель?</b>
Эта идея гласит, средняя продолжительность жизни — около 70 лет, что составляет ~4000 недель.\n
Что ты почувствуешь, если узнаешь, на какой неделе ты <b>сейчас</b>?
<i>Прошёл ли ты уже половину?</i>\n\n
Давай немного поговорим о тебе — <b>как я могу к тебе обращаться?</b>
Можешь написать свой вариант
"""
    
    await message.answer(msg, parse_mode='HTML', reply_markup=get_name_keyboard(message.from_user.full_name, message.from_user.username))
    await UserInit.custom_name.set()


# Обработка имени пользователя
@dp.message_handler(state=UserInit.custom_name)
async def fsm_custom_name(message: types.Message, state: FSMContext):
    if message.text == "Назад":
        if not db.user_exists(message.from_user.id):
            await message.answer("<b>Используй /start для начала</b>", parse_mode='HTML', reply_markup=types.ReplyKeyboardRemove())
        else:
            await message.answer("<b>Используй /reinit для повторной настройки</b>", parse_mode='HTML', reply_markup=types.ReplyKeyboardRemove())
        await state.finish()
        return

    if not message.text:
        await message.answer("Пожалуйста, введи корректное имя", parse_mode='HTML', reply_markup=get_name_keyboard(message.from_user.full_name, message.from_user.username))
        return

    await state.update_data(custom_name=message.text)
    await message.answer("<b>От чего начнём отсчёт?</b>\nНапиши дату рождения в формате DD.MM.YYYY", parse_mode='HTML', reply_markup=get_return_keyboard())
    await UserInit.birthdate.set()


# Обработка даты рождения
@dp.message_handler(state=UserInit.birthdate)
async def fsm_birthdate(message: types.Message, state: FSMContext):
    if message.text == "Назад":
        await message.answer("Давай немного поговорим о тебе — <b>как я могу к тебе обращаться?</b>\nМожешь написать свой вариант", 
                             parse_mode='HTML', reply_markup=get_name_keyboard(message.from_user.full_name, message.from_user.username))
        await UserInit.custom_name.set()
        return

    try:
        # Парсим дату и проверяем её корректность
        birthdate = datetime.strptime(message.text, "%d.%m.%Y").date()

        # Проверяем, чтобы дата не была в будущем
        if birthdate > datetime.today().date():
            await message.answer("Дата рождения не может быть в будущем. Пожалуйста, введите правильную дату.", 
                                 parse_mode='HTML', reply_markup=get_return_keyboard())
            return
    
    except ValueError:
        await message.answer("Введи дату рождения в формате DD.MM.YYYY", parse_mode='HTML', reply_markup=get_return_keyboard())
        return

    await state.update_data(birthdate=birthdate.strftime("%Y-%m-%d"))  # Сохраняем в формате SQL
    await message.answer("<b>Когда мне тебе писать?</b>\nНажми на любой день недели", parse_mode='HTML', reply_markup=get_day_keyboard())
    await UserInit.notify_day.set()


# Обработка дня недели
@dp.message_handler(state=UserInit.notify_day)
async def fsm_notify_day(message: types.Message, state: FSMContext):
    if message.text == "Назад":
        await message.answer("<b>От чего начнём отсчёт?</b>\nНапиши дату рождения в формате DD.MM.YYYY", parse_mode='HTML', reply_markup=get_return_keyboard())
        await UserInit.birthdate.set()
        return

    valid_days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    if message.text not in valid_days:
        await message.answer("Выбери день недели из списка ниже", parse_mode='HTML', reply_markup=get_day_keyboard())
        return

    await state.update_data(notify_day=message.text)
    await message.answer("<b>Во сколько?</b>\nНажми на удобный час", parse_mode='HTML', reply_markup=get_time_keyboard())
    await UserInit.notify_time.set()


# Обработка времени
@dp.message_handler(state=UserInit.notify_time)
async def fsm_notify_time(message: types.Message, state: FSMContext):
    if message.text == "Назад":
        await message.answer("<b>Когда мне тебе писать?</b>\nНажми на любой день недели", parse_mode='HTML', reply_markup=get_day_keyboard())
        await UserInit.notify_day.set()
        return

    try:
        # Парсим время и проверяем его корректность
        notify_time = datetime.strptime(message.text, "%H").time()
    except ValueError:
        await message.answer("Выбери удобный час из списка ниже", parse_mode='HTML', reply_markup=get_time_keyboard())
        return

    await state.update_data(notify_time=notify_time.strftime("%H:%M"))  # Сохраняем в формате SQL

    # Получаем все данные из состояния
    user_data = await state.get_data()

    try:
        # Сохраняем пользователя в базу данных
        if not db.user_exists(message.from_user.id):
            db.add_user(
                user_id=message.from_user.id,
                username=message.from_user.username,
                full_name=message.from_user.full_name,
                custom_name=user_data['custom_name'],
                birthdate=user_data['birthdate'],
                notify_day=user_data['notify_day'],
                notify_time=user_data['notify_time']
            )
            logger.info(f"Добавлен новый пользователь {message.from_user.id}")
        else:
            db.update_user(
                user_id=message.from_user.id,
                custom_name=user_data['custom_name'],
                birthdate=user_data['birthdate'],
                notify_day=user_data['notify_day'],
                notify_time=user_data['notify_time']
            )
            logger.info(f"Обновлена информация для пользователя {message.from_user.id}")

        # Уведомление о текущей неделе
        user_info = {
            'custom_name': user_data['custom_name'],
            'birthdate': user_data['birthdate']
        }
        current_week_message = generate_notification_text(user_info)

        # Обновляем задачу уведомления
        await notifier.update_user_notification(message.from_user.id)

        await message.answer(f"<b>Что-ж...</b> Буду напоминать тебе о скоротечности бытия в <b>{user_data['notify_day']} {user_data['notify_time']}</b>", 
                             parse_mode='HTML', reply_markup=types.ReplyKeyboardRemove())
        await asyncio.sleep(2)

        await message.answer('Чуть не забыл, сейчас пришлю тебе твою <b>текущую неделю</b>', parse_mode='HTML')
        await asyncio.sleep(3)

        await message.answer(current_week_message, parse_mode='HTML')
        await state.finish()
    except Exception as e:
        logger.error(f"Ошибка при сохранении данных пользователя {message.from_user.id}: {e}")
        await message.answer("Произошла ошибка при сохранении данных. Пожалуйста, попробуй ещё раз.")


# Команда /reinit
@dp.message_handler(commands=['reinit'])
async def cmd_reinit(message: types.Message):
    if not db.user_exists(message.from_user.id):
        await message.answer("Ты ещё не зарегистрирован. Используй /start для начала.")
        return
    
    await message.answer("<b>Хочешь что-то изменить?</b>\nОкей. Как я могу к тебе обращаться?", 
                         parse_mode='HTML', reply_markup=get_name_keyboard(message.from_user.full_name, message.from_user.username))
    await UserInit.custom_name.set()
