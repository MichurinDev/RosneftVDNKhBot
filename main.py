# Импорты
from res.config_reader import config
from res.reply_texts import *

from aiogram import Bot, types, Dispatcher, executor
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware

import sqlite3

# Объект бота
TOKEN = config.bot_token.get_secret_value()
ADMIN_TOKEN = config.admin_bot_token.get_secret_value()

bot = Bot(token=TOKEN)
# Диспетчер
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())

# Подгружаем БД
conn = sqlite3.connect('res/data/ProfessionsOfTheFutureOfRosneft_db.db')
cursor = conn.cursor()

# Тип пользователя
user_type = ""

# Кнопки главного меню
buttons = [
    'Создание героя',
    'Профессия',
    'Компетенции',
    'ВУЗы',
    'Обратная связь'
]


# Состояния бота
class BotStates(StatesGroup):
    START_STATE = State()
    HOME_STATE = State()

    SET_NAME_STATE = State()

    GET_SPHERE_STATE = State()
    SET_PROFESSION_STATE = State()

    SET_COMPETENCIES_STATE = State()
    
    SET_UNIVERSITY_STATE = State()


def getValueByTgID(table="UsersInfo", value_column="id", tgID=None):
    if tgID:
        return cursor.execute(f''' SELECT {value_column} FROM
                              {table} WHERE tgId=?''',
                              (tgID,)).fetchall()[0][0]
    else:
        print("ERROR: Telegram ID is None")


# Хэндлер на команду /start
@dp.message_handler(commands=['start'])
async def start(msg: types.Message):
    global user_type

    # Берём список всех зарегистрированных пользователей с выборков по ID
    user_by_tgID = cursor.execute(f''' SELECT tgId FROM UsersInfo
                           WHERE tgId={msg.from_user.id}''').fetchall()

    state = dp.current_state(user=msg.from_user.id)

    if user_by_tgID:
        # Формируем клавиатуру с меню по боту
        keyboard = ReplyKeyboardMarkup()
        for btn in buttons:
            keyboard.add(KeyboardButton(btn))

        # Отправляем ее вместе с приветственным сообщением
        # для зарегистрированного пользователя
        if msg.text == "/start":
            await bot.send_message(
                msg.from_user.id, f"Привет-привет!")

        user_type = getValueByTgID(value_column="type", tgID=msg.from_user.id)

        await bot.send_message(msg.from_user.id,
                               MENU_TEXT, reply_markup=keyboard)
        await state.set_state(BotStates.HOME_STATE.state)

    else:
        # Отправляем текст с ошибкой
        await bot.send_message(
            msg.from_user.id,
            ADMINISTRATOR_ACCESS_ERROR
        )


# Хэндлер на команду /help
@dp.message_handler(commands=['help'])
async def help(msg: types.Message):
    await bot.send_message(msg.from_user.id, HELP_TEXT)


# Хэндлер на текстовые сообщения
@dp.message_handler(state=BotStates.HOME_STATE)
async def reply_to_text_msg(msg: types.Message):
    if msg.text == buttons[0]:
        await bot.send_message(msg.from_user.id,
                               "Введите следующую информацию в указаном формате:\n"+
                               "Имя\nПол\nВозраст\nУвлечения (увлечение 1, увлечение 2...)\n"+
                               "Населённый пункт старта жизненного пути")
        state = dp.current_state(user=msg.from_user.id)
        await state.set_state(BotStates.SET_NAME_STATE.state)

    elif msg.text == buttons[1]:
        await bot.send_message(msg.from_user.id,
                               "Выберите сферу профессии:")
        state = dp.current_state(user=msg.from_user.id)
        await state.set_state(BotStates.GET_SPHERE_STATE.state)

    elif msg.text == buttons[2]:
        await bot.send_message(msg.from_user.id,
                               "Напишите имеющиеся компетенции:")
        state = dp.current_state(user=msg.from_user.id)
        await state.set_state(BotStates.SET_COMPETENCIES_STATE.state)

    elif msg.text == buttons[3]:
        await bot.send_message(msg.from_user.id,
                               "Выберите ВУЗ:")
        state = dp.current_state(user=msg.from_user.id)
        await state.set_state(BotStates.SET_UNIVERSITY_STATE.state)

    elif msg.text == buttons[4]:
        form_url = "Ссылка на форму"
        await bot.send_message(msg.from_user.id, form_url)
    elif msg.text == "/start":
        await start(msg)
    elif msg.text == "/help":
        await help(msg)


@dp.message_handler(state=BotStates.SET_NAME_STATE)
async def set_name(msg: types.Message):
    try:
        # Получаем информацию
        info = msg.text.split("\n")

        # Заполняем строку в БД
        cursor.execute("""UPDATE Teams SET
                    name=?, sex=?, age=?, hobby=?, city=?
                    WHERE facilitatorId=?""",
                    (info[0], info[1], info[2], info[3], info[4], msg.from_user.id))
        conn.commit()

        # Отправляем сообщение об успешном добавлении
        await bot.send_message(msg.from_user.id, "Ответ принят!")
    except Exception as e:
        # Если возникла ошибка
        await bot.send_message(msg.from_user.id, "Произошла ошибка!")
        print(e)

    # Переходим в главное меню
    state = dp.current_state(user=msg.from_user.id)
    await state.set_state(BotStates.START_STATE)
    await start(msg)


@dp.message_handler(state=BotStates.GET_SPHERE_STATE)
async def get_sphere(msg: types.Message):
    # Формируем клавиатуру с профессиями по сфере
    profs = cursor.execute("""SELECT name FROM Professions WHERE sphere=?""", (msg.text,))
    kb = ReplyKeyboardMarkup()
    for i in profs:
        kb.add(i[0])

    # Отправляем сообщение
    await bot.send_message(msg.from_user.id, "Выберите профессию на клавиатуре снизу или введите своё:", reply_markup=kb)

    # Переходим на стадию выбора профессии
    state = dp.current_state(user=msg.from_user.id)
    await state.set_state(BotStates.SET_PROFESSION_STATE.state)

@dp.message_handler(state=BotStates.SET_PROFESSION_STATE)
async def set_profession(msg: types.Message):
    prof = msg.text
    try:
        # Заполняем строку в БД
        cursor.execute("""UPDATE Teams SET profession=? WHERE facilitatorId=?""",
                    (prof, msg.from_user.id))
        conn.commit()

        # Отправляем сообщение об успешном добавлении
        await bot.send_message(msg.from_user.id, "Ответ принят!")
    except Exception as e:
        # Если возникла ошибка
        await bot.send_message(msg.from_user.id, "Произошла ошибка!")
        print(e)

    # Переходим в главное меню
    state = dp.current_state(user=msg.from_user.id)
    await state.set_state(BotStates.START_STATE)
    await start(msg)

@dp.message_handler(state=BotStates.SET_COMPETENCIES_STATE)
async def set_competencies(msg: types.Message):
    # Получаем информацию
    competencies = msg.text

    try:
        # Заполняем строку в БД
        cursor.execute("""UPDATE Teams SET competencies=? WHERE facilitatorId=?""",
                    (competencies, msg.from_user.id))
        conn.commit()

        # Отправляем сообщение об успешном добавлении
        await bot.send_message(msg.from_user.id, "Ответ принят!")
    except Exception as e:
        # Если возникла ошибка
        await bot.send_message(msg.from_user.id, "Произошла ошибка!")
        print(e)

    # Переходим в главное меню
    state = dp.current_state(user=msg.from_user.id)
    await state.set_state(BotStates.START_STATE)
    await start(msg)


@dp.message_handler(state=BotStates.SET_UNIVERSITY_STATE)
async def set_university(msg: types.Message):
    # Получаем информацию
    university = msg.text

    try:
        # Заполняем строку в БД
        cursor.execute("""UPDATE Teams SET university=? WHERE facilitatorId=?""",
                    (university, msg.from_user.id))
        conn.commit()

        # Отправляем сообщение об успешном добавлении
        await bot.send_message(msg.from_user.id, "Ответ принят!")
    except Exception as e:
        # Если возникла ошибка
        await bot.send_message(msg.from_user.id, "Произошла ошибка!")
        print(e)

    # Переходим в главное меню
    state = dp.current_state(user=msg.from_user.id)
    await state.set_state(BotStates.START_STATE)
    await start(msg)


# Запуск бота
if __name__ == '__main__':
    print("Бот запущен...")
    executor.start_polling(dp, skip_updates=False)
