# Импорты
from modules.config_reader import config
from modules.reply_texts import *

from aiogram import Bot, types, Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

import sqlite3

TOKEN = config.bot_token.get_secret_value()
ADMIN_TOKEN = config.admin_bot_token.get_secret_value()


# Состояния бота
class BotStates(StatesGroup):
    START_STATE = State()
    HOME_STATE = State()

# Объект бота
bot = Bot(token=ADMIN_TOKEN)

# Диспетчер
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())

# Подгружаем БД
conn = sqlite3.connect('res/data/ProfessionsOfTheFutureOfRosneft_db.db')
cursor = conn.cursor()

buttons = [
    'Выгрузить карточки команд',
    'Сброс данных'
]

user_type = ""


# Хэндлер на команду /start
@dp.message_handler(commands=['start'])
async def start(msg: types.Message):
    global user_type

    # Берём список всех зарегистрированных пользователей с выборков по ID
    user_by_tgID = cursor.execute(f''' SELECT type FROM UsersInfo WHERE tgId={msg.from_user.id}''').fetchall()

    if user_by_tgID:
        # Формируем клавиатуру с меню по боту
        keyboard = ReplyKeyboardMarkup()
        for bnt in buttons:
            keyboard.add(KeyboardButton(bnt))

        # Отправляем ее вместе с приветственным сообщением
        # для зарегистрированного пользователя
        if msg.text == "/start":
            await bot.send_message(
                msg.from_user.id, f"Здравствуйте!")

        user_type = user_by_tgID[0][0]

        await bot.send_message(msg.from_user.id, "Выберите действие:", reply_markup=keyboard)

        state = dp.current_state(user=msg.from_user.id)
        await state.set_state(BotStates.HOME_STATE.state)

    else:
        # Отправляем текст с ошибкой
        await bot.send_message(msg.from_user.id, ADMINISTRATOR_ACCESS_ERROR)


# Состояние главного меню
@dp.message_handler(state=BotStates.HOME_STATE)
async def home(msg: types.Message):
    if msg.text == buttons[0]:
        if user_type in ["Администратор", "Ведущий"]:
            await bot.send_message(msg.from_user.id, "Формирование карточек")
        else:
            await bot.send_message(msg.from_user.id, ADMINISTRATOR_ACCESS_ERROR)

    elif msg.text == buttons[1]:
        if user_type in ["Администратор"]:
            info = cursor.execute("""SELECT facilitatorId from Teams""").fetchall()

            for i in info:
                fal = i[0]
                
                # Сбрасываем нужные значения строку в БД
                cursor.execute("""UPDATE Teams SET
                            name=?, sex=?, age=?, hobby=?, city=?, profession=?,
                            competencies=?, university=?, specialties=? WHERE facilitatorId=?""",
                            (None, None, None, None, None, None, None, None, None, fal))
            conn.commit()

            await bot.send_message(msg.from_user.id, "Информация сброшена!")
        else:
            await bot.send_message(msg.from_user.id, ADMINISTRATOR_ACCESS_ERROR)

    elif msg.text == "/start":
        await start(msg)


# Запуск бота
if __name__ == '__main__':
    print("Бот запущен...")
    executor.start_polling(dp, skip_updates=False)
