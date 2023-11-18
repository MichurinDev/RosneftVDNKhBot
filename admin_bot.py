# Импорты
from res.config_reader import config
from res.reply_texts import *
from res.SendNotify import send_notify

from aiogram import Bot, types, Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, ParseMode, \
    ContentType

import sqlite3
import json

TOKEN = config.bot_token.get_secret_value()
ADMIN_TOKEN = config.admin_bot_token.get_secret_value()


# Состояния бота
class BotStates(StatesGroup):
    START_STATE = State()
    HOME_STATE = State()
    ACQUAINTANCE_STATE = State()

    SEND_MESSAGE_STATE = State()

    CHOICE_EVENT_STATE = State()
    UPLOAD_PARTICIPANTS_LIST_STATE = State()

    CHOICE_QUEST_ACTION_STATE = State()

    CHOICE_EVENT_TO_SWITCH_ENTRY = State()

    CHOICE_MSG_TO_SUPPORT = State()
    SEND_REPLY_TO_SUPPORT_MSG = State()

    CHANGE_USER_CITY = State()


# Объект бота
bot = Bot(token=ADMIN_TOKEN)
# Диспетчер
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())

# Подгружаем БД
conn = sqlite3.connect('res/data/ProfessionsOfTheFutureOfRosneft_db.db')
cursor = conn.cursor()

buttons = [
    'Сменить город',
    'Отправить сообщение участникам форума',
    'Выгрузить список участников воркшопов',
    'Список команд для квеста',
    'Рейтинг мероприятий',
    'Открыть/закрыть запись на воркшопы',
    'Сообщения в поддержку'
]

user_city = ""
user_type = ""
_temp = None


# Хэндлер на команду /start
@dp.message_handler(commands=['start'])
async def start(msg: types.Message):
    global user_city, user_type

    # Берём список всех зарегистрированных пользователей с выборков по ID
    user_by_tgID = cursor.execute(f''' SELECT city, type FROM UsersInfo
                           WHERE tg_id={msg.from_user.id}''').fetchall()

    state = dp.current_state(user=msg.from_user.id)

    if user_by_tgID:
        user_by_tgID = user_by_tgID[0]

        # Формируем клавиатуру с меню по боту
        keyboard = ReplyKeyboardMarkup()
        for bnt in buttons:
            keyboard.add(KeyboardButton(bnt))

        # Отправляем ее вместе с приветственным сообщением
        # для зарегистрированного пользователя
        if msg.text == "/start":
            await bot.send_message(
                msg.from_user.id, f"Здравсвуйте!")

        user_city, user_type = user_by_tgID

        await bot.send_message(msg.from_user.id,
                               f"Город: {user_city}\n" +
                               f"Роль: {user_type}\n" +
                               "Выберите действие:", reply_markup=keyboard)
        await state.set_state(BotStates.HOME_STATE.state)

    else:
        # Отправляем текст с предложением ввести ID
        await bot.send_message(
            msg.from_user.id,
            "Здравствуйте!")

        # Переходим на стадию ввода ФИО
        await bot.send_message(msg.from_user.id, "Введите Ваш ID")
        await state.set_state(BotStates.ACQUAINTANCE_STATE.state)


@dp.message_handler(state=BotStates.ACQUAINTANCE_STATE)
async def acquaintance(msg: types.Message):
    # Если пользователь с введёным ID существует
    if cursor.execute('''SELECT name FROM UsersInfo WHERE id=?
                      AND tg_id IS NULL''', (msg.text,)).fetchall():
        # Добавляем нового пользователя
        cursor.execute('''UPDATE UsersInfo SET tg_id=?
                       WHERE id=? AND tg_id IS NULL''',
                       (msg.from_user.id, msg.text))
        conn.commit()

        # Возвращаемся в главное меню
        state = dp.current_state(user=msg.from_user.id)
        await state.set_state(BotStates.START_STATE)
        await start(msg)
    # А если не существует
    else:
        await bot.send_message(msg.from_user.id,
                               "ID не найден! Введите еще раз")


# Состояние главного меню
@dp.message_handler(state=BotStates.HOME_STATE)
async def home(msg: types.Message):
    if msg.text == buttons[0]:
        if user_type in ['Администратор']:
            cities = cursor.execute('''SELECT city
                                    FROM ForumCities''').fetchall()
            keyboard = ReplyKeyboardMarkup()

            for city in cities:
                keyboard.add(city[0])
            keyboard.add("В главное меню")

            await bot.send_message(msg.from_user.id,
                                   f"Текущий город: {user_city}\n" +
                                   "Выберите город:",
                                   reply_markup=keyboard)

            state = dp.current_state(user=msg.from_user.id)
            await state.set_state(BotStates.CHANGE_USER_CITY.state)
        else:
            await bot.send_message(msg.from_user.id,
                                   ADMINISTRATOR_ACCESS_ERROR)

            state = dp.current_state(user=msg.from_user.id)
            await state.set_state(BotStates.START_STATE.state)
            await start(msg)
    elif msg.text == buttons[1]:
        if user_type in ['Администратор']:
            keyboard = ReplyKeyboardMarkup()\
                .add(KeyboardButton("Шаблоны"))\
                .add(KeyboardButton("В главное меню"))
            await bot.send_message(msg.from_user.id, "Введите сообщение:",
                                   reply_markup=keyboard)

            state = dp.current_state(user=msg.from_user.id)
            await state.set_state(BotStates.SEND_MESSAGE_STATE.state)
        else:
            await bot.send_message(msg.from_user.id,
                                   ADMINISTRATOR_ACCESS_ERROR)

            state = dp.current_state(user=msg.from_user.id)
            await state.set_state(BotStates.START_STATE.state)
            await start(msg)
    elif msg.text == buttons[2]:
        if user_type in ['Администратор', 'Волонтёр']:
            # Берём названия мероприятий в нужном городе
            events_titles_list = \
                list(map(lambda x: x[0],
                         cursor.execute('''SELECT title FROM Workshops
                                        WHERE city=?''',
                                        (user_city,)).fetchall()))

            # Формируем клавиатуру
            keyboard = ReplyKeyboardMarkup()
            for bnt in events_titles_list:
                keyboard.add(KeyboardButton(bnt))
            keyboard.add(KeyboardButton("В главное меню"))

            await bot.send_message(msg.from_user.id, "Выберите воркшоп:",
                                   reply_markup=keyboard)

            state = dp.current_state(user=msg.from_user.id)
            await state.set_state(BotStates.CHOICE_EVENT_STATE.state)
        else:
            await bot.send_message(msg.from_user.id,
                                   ADMINISTRATOR_ACCESS_ERROR)
            state = dp.current_state(user=msg.from_user.id)
            await state.set_state(BotStates.START_STATE.state)
            await start(msg)
    elif msg.text == buttons[3]:
        if user_type in ['Администратор', 'Волонтёр']:
            # Открываем JSON с информацией о командах для квеста
            with open('./res/data/quest_commands.json',
                      'r', encoding='utf-8') as quest_commands:
                # Читаем файл
                data = json.load(quest_commands)

            send_message = ""
            for team in data[user_city]:
                # ФИО участников мерпориятия по ID: [ФИО1, ФИО2...]
                if team != "students":
                    ids_str = ','.join(list(map(str, data[user_city][team])))
                    teamers_list = \
                        [x[0] for x in cursor
                         .execute(f'''SELECT name FROM UsersInfo
                                WHERE id in ({ids_str})''').fetchall()]

                    # Формируем сообщение
                    send_message += f"\n\n{team} " +\
                        "({len(teamers_list)} человек):"
                    for user in teamers_list:
                        send_message += f"\n- {user}"
                else:
                    students_teams = team
                    for student_team in data[user_city][students_teams]:
                        ids_str = ','.join(list(map(str, data[user_city]
                                                    ["students"][student_team]
                                                    )))
                        teamers_list = \
                            [x[0] for x in cursor
                             .execute(f'''SELECT name FROM UsersInfo
                                    WHERE id in ({ids_str})''').fetchall()]

                        # Формируем сообщение
                        send_message += f"\n\n{student_team} " +\
                            f"({len(teamers_list)} человек):"
                        for user in teamers_list:
                            send_message += f"\n- {user}"

            # Отправляем сообщение
            await bot.send_message(msg.from_user.id, send_message)
        else:
            await bot.send_message(msg.from_user.id,
                                   ADMINISTRATOR_ACCESS_ERROR)

        state = dp.current_state(user=msg.from_user.id)
        await state.set_state(BotStates.START_STATE.state)
        await start(msg)
    elif msg.text == buttons[4]:
        if user_type in ['Администратор']:
            events = cursor.execute(f''' SELECT title, scores
                                    FROM Events WHERE city=?''',
                                    (user_city,)).fetchall()
            send_text = "Рейтинги мероприятий:"
            for event in events:
                if event[1]:
                    rating = round(sum(list(map(int,
                                                event[1].split(";")[:-1]))) /
                                   len(list(map(int,
                                                event[1].split(";")[:-1]))),
                                   1)
                else:
                    rating = float(0)
                send_text += f"\n- {event[0]}: {rating}/5.0"

            await bot.send_message(msg.from_user.id, send_text)
        else:
            await bot.send_message(msg.from_user.id,
                                   ADMINISTRATOR_ACCESS_ERROR)

        state = dp.current_state(user=msg.from_user.id)
        await state.set_state(BotStates.START_STATE.state)
        await start(msg)
    elif msg.text == buttons[5]:
        if user_type in ['Администратор']:
            events = cursor.execute("""SELECT title, entryIsOpen
                                    FROM Workshops WHERE city=?""",
                                    (user_city,)).fetchall()
            send_text = "Выберите мероприятие:"
            keyboard = ReplyKeyboardMarkup()

            for event in events:
                entry_emoj = None
                if event[1] == 1:
                    entry_emoj = "✅"
                else:
                    entry_emoj = "❌"

                send_text += f"\n- {event[0]} - {entry_emoj}"
                keyboard.add(KeyboardButton(event[0]))

            keyboard.add("В главное меню")

            await bot.send_message(msg.from_user.id,
                                   send_text,
                                   reply_markup=keyboard)

            state = dp.current_state(user=msg.from_user.id)
            await state.set_state(BotStates.CHOICE_EVENT_TO_SWITCH_ENTRY.state)
        else:
            await bot.send_message(msg.from_user.id,
                                   ADMINISTRATOR_ACCESS_ERROR)

            state = dp.current_state(user=msg.from_user.id)
            await state.set_state(BotStates.START_STATE.state)
            await start(msg)
    elif msg.text == buttons[6]:
        if user_type in ['Администратор']:
            messages = cursor.execute(f'''SELECT id, user_id, name, message
                                      FROM MsgToSupport WHERE city=?
                                      AND isSolved=0''', (user_city,))\
                                        .fetchall()
            if messages:
                send_text = "Обращения в поддержку:\n-----"
                keyboard = ReplyKeyboardMarkup()

                for message in messages:
                    send_text += f"\nID вопроса: {message[0]}" +\
                        f"\nID участника: {message[1]}" +\
                        f"\nИмя: {message[2]}" +\
                        f"\nСообщение: {message[3][:20]}"
                    send_text += "\n-----"

                    keyboard.add(str(message[0]))

                keyboard.add("В главное меню")

                await bot.send_message(msg.from_user.id, send_text,
                                       reply_markup=keyboard)

                state = dp.current_state(user=msg.from_user.id)
                await state.set_state(BotStates.CHOICE_MSG_TO_SUPPORT.state)
            else:
                await bot.send_message(msg.from_user.id,
                                       "Обращений в службу поддержки" +
                                       " не найдено")
        else:
            await bot.send_message(msg.from_user.id,
                                   ADMINISTRATOR_ACCESS_ERROR)

            state = dp.current_state(user=msg.from_user.id)
            await state.set_state(BotStates.START_STATE.state)
            await start(msg)
    elif msg.text == "/start":
        await start(msg)


# Отправка сообщений участникам форума от лица "клиентского" бота
@dp.message_handler(state=BotStates.SEND_MESSAGE_STATE)
async def send_msg_to_users(msg: types.Message):
    if msg.text != "В главное меню":
        if msg.text != "Шаблоны":
            # Список ID зарегистрированных пользователей
            users = cursor.execute('''SELECT tg_id FROM UsersInfo
                                   WHERE city=? AND tg_id <> ?''',
                                   (user_city, "None")).fetchall()

            await bot.send_message(msg.from_user.id, "Отправка...")

            # Перебираем ID зарегистрированных пользоателей
            for user in users:
                if user != msg.from_user.id:
                    # Отправляем сообщение пользователю
                    send_notify(token=TOKEN, msg=msg.text, chatId=user[0])

            await bot.send_message(msg.from_user.id, "Сообщение отправлено!")

            # Выходим в главное меню
            state = dp.current_state(user=msg.from_user.id)
            await state.set_state(BotStates.HOME_STATE.state)
            await start(msg)
        else:
            await bot.send_message(msg.from_user.id, NOTIFY_PATTERN_TEXT,
                                   parse_mode=ParseMode.HTML)
    else:
        # Выходим в главное меню
        state = dp.current_state(user=msg.from_user.id)
        await state.set_state(BotStates.HOME_STATE.state)
        await start(msg)


@dp.message_handler(state=BotStates.CHOICE_EVENT_STATE)
async def get_parts_by_event_title(msg: types.Message):
    if msg.text != "В главное меню":
        # Читаем JSON-файл с участниками мероприятий
        with open('./res/data/participants_of_events.json',
                  'r', encoding='utf-8') as participants_of_events:
            # Читаем файл
            data = json.load(participants_of_events)

        if msg.text in data[user_city]:
            # Список ID участников мероприятия
            participants = data[user_city][msg.text]
            # ФИО участников мерпориятия по ID: [ФИО1, ФИО2...]
            usernames = [x[0] for x in cursor.execute(
                f''' SELECT name FROM UsersInfo
                WHERE id in ({','.join(list(map(str, participants)))})'''
                ).fetchall()]

            # Формируем сообщение
            send_text = f"Участники мероприятия \"{msg.text}\" " + \
                f"({len(usernames)} человек):"
            for user in usernames:
                send_text += f"\n- {user}"

            # Отправляем сообщение
            await bot.send_message(msg.from_user.id, send_text)
        else:
            await bot.send_message(msg.from_user.id,
                                   f"На мероприятие \"{msg.text}\" еще никто" +
                                   " не зарегистрировался!")

    # Выходим в главное меню
    state = dp.current_state(user=msg.from_user.id)
    await state.set_state(BotStates.HOME_STATE.state)
    await start(msg)


@dp.message_handler(state=BotStates.CHOICE_EVENT_TO_SWITCH_ENTRY)
async def send_msg_to_users(msg: types.Message):
    if msg.text != "В главное меню":
        currentEntryIsOpen = cursor.execute('''SELECT
                                            entryIsOpen FROM Workshops
                                            WHERE title=? AND city=?''',
                                            (msg.text, user_city)).fetchall()

        if currentEntryIsOpen:
            currentEntryIsOpen = currentEntryIsOpen[0][0]
            if currentEntryIsOpen == 1:
                cursor.execute('''UPDATE Workshops SET entryIsOpen=?
                               WHERE title=? AND city=?''',
                               (0, msg.text, user_city))
            elif currentEntryIsOpen == 0:
                cursor.execute('''UPDATE Workshops SET entryIsOpen=?
                               WHERE title=? AND city=?''',
                               (1, msg.text, user_city))
            conn.commit()

            await bot.send_message(msg.from_user.id,
                                   "Статус регистрации на воркшоп обновлён!")
            # Выходим в главное меню
            state = dp.current_state(user=msg.from_user.id)
            await state.set_state(BotStates.HOME_STATE.state)
            await start(msg)
        else:
            await bot.send_message(msg.from_user.id, "Мероприятие не найдено!")
    else:
        # Выходим в главное меню
        state = dp.current_state(user=msg.from_user.id)
        await state.set_state(BotStates.HOME_STATE.state)
        await start(msg)


@dp.message_handler(state=BotStates.CHOICE_MSG_TO_SUPPORT)
async def send_msg_to_users(msg: types.Message):
    global _temp

    if msg.text != "В главное меню":
        message = cursor.execute('''SELECT message FROM MsgToSupport
                                 WHERE id=?''', (msg.text,)).fetchall()
        if message:
            message = message[0][0]
            send_text = f"Сообщение:\n{message}"

            _temp = msg.text

            await bot.send_message(msg.from_user.id, send_text)

            keyboard = ReplyKeyboardMarkup().add("В главное меню")
            await bot.send_message(msg.from_user.id,
                                   "Отправьте ответное сообщение:",
                                   reply_markup=keyboard)

            state = dp.current_state(user=msg.from_user.id)
            await state.set_state(BotStates.SEND_REPLY_TO_SUPPORT_MSG.state)
        else:
            await bot.send_message(msg.from_user.id, "Обращение не найдено")
    else:
        # Выходим в главное меню
        state = dp.current_state(user=msg.from_user.id)
        await state.set_state(BotStates.HOME_STATE.state)
        await start(msg)


@dp.message_handler(state=BotStates.SEND_REPLY_TO_SUPPORT_MSG)
async def send_msg_to_users(msg: types.Message):
    global _temp

    if msg.text != "В главное меню":
        user_tg_id, message = cursor.execute(f'''SELECT tg_id, message FROM
                                    MsgToSupport WHERE id=?''', (_temp,))\
                                        .fetchall()[0]

        send_text = f"Ответ на твоё обращение:\n" +\
            f"Твоё сообщение: {message}\n" +\
            f"Ответ от поддержки: {msg.text}"
        send_notify(TOKEN, send_text, user_tg_id)
        await bot.send_message(msg.from_user.id, "Сообщение отправлено!")

        cursor.execute(f'''UPDATE MsgToSupport SET isSolved=1 WHERE id=?''',
                       (_temp,))
        conn.commit()

        _temp = None
    # Выходим в главное меню
    state = dp.current_state(user=msg.from_user.id)
    await state.set_state(BotStates.HOME_STATE.state)
    await start(msg)


@dp.message_handler(state=BotStates.CHANGE_USER_CITY)
async def send_msg_to_users(msg: types.Message):
    if msg.text != "В главное меню":
        cities = list(map(lambda x: x[0],
                          cursor.execute('''SELECT city FROM
                                         ForumCities''').fetchall()))
        if msg.text in cities:
            cursor.execute(f'''UPDATE UsersInfo SET city=? WHERE tg_id=?''',
                           (msg.text, msg.from_user.id))
            conn.commit()

            await bot.send_message(msg.from_user.id,
                                   f"Ваш город изменён на {msg.text}")

            # Выходим в главное меню
            state = dp.current_state(user=msg.from_user.id)
            await state.set_state(BotStates.HOME_STATE.state)
            await start(msg)
        else:
            await bot.send_message(msg.from_user.id, "Город не найден!")
    else:
        # Выходим в главное меню
        state = dp.current_state(user=msg.from_user.id)
        await state.set_state(BotStates.HOME_STATE.state)
        await start(msg)

# Запуск бота
if __name__ == '__main__':
    print("Бот запущен...")
    executor.start_polling(dp, skip_updates=False)
