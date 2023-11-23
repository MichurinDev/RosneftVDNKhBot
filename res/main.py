# Импорты
from modules.config_reader import config
from modules.reply_texts import *

from aiogram import Bot, types, Dispatcher, executor
from aiogram.types import ReplyKeyboardRemove, KeyboardButton,\
    ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
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

# Временные данные
_temp = None

# Тип пользователя
user_type = ""
user_msg = ""

# Кнопки главного меню
buttons = [
    'Создание героя',
    'Профессия',
    'Компетенции',
    'ВУЗ',
    'Специальность',
    'Обратная связь'
]


# Состояния бота
class BotStates(StatesGroup):
    START_STATE = State()
    HOME_STATE = State()

    SET_NAME_STATE = State()

    GET_SPHERE_STATE = State()
    SET_PROFESSION_STATE = State()
    SET_OTHER_PROFESSION_STATE = State()

    GET_SPHERE_COMPETENCIES_STATE = State()
    SET_COMPETENCIES_STATE = State()
    SET_OTHER_COMPETENCIES_STATE = State()
    
    SET_UNIVERSITY_STATE = State()

    GET_SPECIALITES_SPHERE_STATE = State()
    SET_SPECIALTIES_STATE = State()


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
    global user_type, user_msg

    # Берём список всех зарегистрированных пользователей с выборков по ID
    user_by_tgID = cursor.execute(f''' SELECT tgId FROM UsersInfo
                           WHERE tgId={msg.from_user.id}''').fetchall()

    if user_by_tgID:
        user_msg = msg

        # Формируем клавиатуру с меню по боту
        keyboard = ReplyKeyboardMarkup()
        for btn in buttons:
            keyboard.add(KeyboardButton(btn))

        # Отправляем ее вместе с приветственным сообщением
        # для зарегистрированного пользователя
        if msg.text == "/start":
            await bot.send_message(
                msg.from_user.id, f"Здравствуйте!")

        user_type = getValueByTgID(value_column="type", tgID=msg.from_user.id)

        await bot.send_message(msg.from_user.id,
                               MENU_TEXT, reply_markup=keyboard)

        state = dp.current_state(user=msg.from_user.id)
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
                               "Имя\nПол (Мужской/женский)\nВозраст\nУвлечения (увлечение 1, увлечение 2...)\n"+
                               "Любимые школьные предметы (предмет 1, предмет 2...)\n"+
                               "Населённый пункт старта жизненного пути")
        state = dp.current_state(user=msg.from_user.id)
        await state.set_state(BotStates.SET_NAME_STATE.state)

    elif msg.text == buttons[1]:
        # Формируем клавиатуру со сферами профессий
        spheres = set([i[0] for i in cursor.execute("""SELECT sphere FROM Professions""")])
        kb = ReplyKeyboardMarkup()
        for i in spheres:
            kb.add(i)

        await bot.send_message(msg.from_user.id,
                               "Выберите сферу профессии:", reply_markup=kb)

        state = dp.current_state(user=msg.from_user.id)
        await state.set_state(BotStates.GET_SPHERE_STATE.state)

    elif msg.text == buttons[2]:
        # Формируем клавиатуру со сферами компетенций
        spheres = set([i[0] for i in cursor.execute("""SELECT sphere FROM Сompetencies""")])
        kb = ReplyKeyboardMarkup()
        for i in spheres:
            kb.add(i)

        await bot.send_message(msg.from_user.id,
                               "Выберите сферу компетенций:", reply_markup=kb)

        state = dp.current_state(user=msg.from_user.id)
        await state.set_state(BotStates.GET_SPHERE_COMPETENCIES_STATE.state)

    elif msg.text == buttons[3]:
        # Формируем клавиатуру с ВУЗами
        spheres = set([i[0] for i in cursor.execute("""SELECT name FROM Universities""").fetchall()])
        if spheres:
            kb = ReplyKeyboardMarkup()
            for i in spheres:
                kb.add(i)
        else:
            kb = ReplyKeyboardMarkup()

        await bot.send_message(msg.from_user.id,
                               "Выберите ВУЗ на клавиатуре снизу или введите свой:",
                               reply_markup=kb)

        state = dp.current_state(user=msg.from_user.id)
        await state.set_state(BotStates.SET_UNIVERSITY_STATE.state)

    elif msg.text == buttons[4]:
        # Формируем клавиатуру с ВУЗами
        spheres = set([i[0] for i in cursor.execute("""SELECT sphere FROM Specialites""").fetchall()])
        if spheres:
            kb = ReplyKeyboardMarkup()
            for i in spheres:
                kb.add(i)
        else:
            kb = ReplyKeyboardMarkup()

        await bot.send_message(msg.from_user.id,
                               "Выберите категорию специальности на клавиатуре снизу:",
                               reply_markup=kb)

        state = dp.current_state(user=msg.from_user.id)
        await state.set_state(BotStates.GET_SPECIALITES_SPHERE_STATE.state)

    elif msg.text == buttons[5]:
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
                    name=?, sex=?, age=?, hobby=?, favoriteSubjects=?, city=?
                    WHERE facilitatorId=?""",
                    (info[0], info[1], info[2], info[3], info[4], info[5],
                     msg.from_user.id))
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
    profs = cursor.execute("""SELECT name FROM Professions WHERE sphere=?""",
                           (msg.text,))
    if profs:
        kb = ReplyKeyboardMarkup()
        for i in profs:
            kb.add(i[0])
        kb.add("Другое")
        kb.add("Назад")
    else:
        kb = ReplyKeyboardRemove()

    # Отправляем сообщение
    await bot.send_message(msg.from_user.id,
                        "Выберите профессию на клавиатуре снизу или введите своё:",
                        reply_markup=kb)

    # Переходим на стадию выбора профессии
    state = dp.current_state(user=msg.from_user.id)
    await state.set_state(BotStates.SET_PROFESSION_STATE.state)

@dp.message_handler(state=BotStates.SET_PROFESSION_STATE)
async def set_profession(msg: types.Message):
    prof = msg.text
    if prof == "Назад":
        # Переходим на выбор сферы
        state = dp.current_state(user=msg.from_user.id)
        await state.set_state(BotStates.HOME_STATE)
        await start(msg)
    elif prof == "Другое":
            await bot.send_message(user_msg.from_user.id,
                                   "Напишите совю профессию:")

            # Переходим на стадию приёма произвольного ответа
            state = dp.current_state(user=user_msg.from_user.id)
            await state.set_state(BotStates.SET_OTHER_PROFESSION_STATE)
    else:
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


@dp.message_handler(state=BotStates.SET_OTHER_PROFESSION_STATE)
async def get_competencies_sphere(msg: types.Message):
    # Получаем информацию
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


@dp.message_handler(state=BotStates.GET_SPHERE_COMPETENCIES_STATE)
async def get_competencies_sphere(msg: types.Message):
    global _temp
    # Формируем клавиатуру с компетенциями по сфере
    comps = [p[0] for p in cursor.execute("""SELECT name
                                          FROM Сompetencies WHERE sphere=?""",
                                          (msg.text,)).fetchall()]
    _temp = comps

    kb = InlineKeyboardMarkup()
    for i in comps:
        if i != None:
            kb.add(InlineKeyboardButton(i, callback_data=i[:20]))
    kb.add(InlineKeyboardButton("Другое", callback_data="Другое"))

    # Отправляем сообщение
    await bot.send_message(msg.from_user.id,
                           "Компетенции на клавиатуре снизу или введите своё, нажав «Другое»",
                           reply_markup=ReplyKeyboardRemove())
    await bot.send_message(msg.from_user.id, "Компетенции:", reply_markup=kb)

    # Переходим на стадию выбора компетенций
    state = dp.current_state(user=msg.from_user.id)
    await state.set_state(BotStates.SET_COMPETENCIES_STATE.state)


@dp.callback_query_handler(state=BotStates.SET_COMPETENCIES_STATE)
async def set_competencies(callback_query: types.CallbackQuery):
    global _temp

    # Получаем текущую инлайн-клавиатуру
    current_keyboard = callback_query.message.reply_markup.inline_keyboard

    callback_query.data = callback_query.data[:25]

    if callback_query.data != "Далее":
        if callback_query.data != "Другое":
            # Находим индекс кнопки, которую хотим изменить
            button_index = None

            for i, row in enumerate(current_keyboard):
                for j, button in enumerate(row):
                    if button.callback_data == callback_query.data:
                        button_index = (i, j)
                        break

            # Изменяем текст кнопки, добавляя эмоджи
            if button_index is not None:
                if " ✅" in current_keyboard[button_index[0]][button_index[1]].text:
                    current_keyboard[button_index[0]][button_index[1]].text =\
                        callback_query.data.replace(" ✅", "")
                else:
                    current_keyboard[button_index[0]][button_index[1]].text =\
                        callback_query.data + " ✅"

            if current_keyboard[-1][0].text != 'Далее ➡️':
                callback_query.message.reply_markup.add(
                    InlineKeyboardButton('Далее ➡️',
                                        callback_data='Далее'))
            # Редактируем сообщение, заменяя только клавиатуру
            await bot.edit_message_reply_markup(
                chat_id=callback_query.message.chat.id,
                message_id=callback_query.message.message_id,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=current_keyboard)
            )
        else:
            await bot.send_message(user_msg.from_user.id,
                                   "Отправьте компетенции ниже через запятую:")

            # Переходим на стадию приёма произвольного ответа
            state = dp.current_state(user=user_msg.from_user.id)
            await state.set_state(BotStates.SET_OTHER_COMPETENCIES_STATE)
    else:
        await bot.edit_message_reply_markup(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            reply_markup=None  # Это уберет старую клавиатуру
        )

        # Сохраняем выбранные предметы
        comps = [k[:-2] for k in list(map(lambda x: x[0].text,
                                            current_keyboard)) if "✅" in k]
        all_comps = cursor.execute("""SELECT name FROM Сompetencies""").fetchall()

        for i in range(len(comps)):
            for j in all_comps:
                if j[0] != None:
                    if comps[i] in j[0]:
                        comps[i] = j[0]
            
        now_comps = cursor.execute("""SELECT competencies FROM Teams WHERE facilitatorId=?""",
                           (user_msg.from_user.id,)).fetchall()

        if now_comps[0][0] != "":
            comps += now_comps[0][0].split(", ")
        
        try:
            cursor.execute("""UPDATE Teams SET competencies=? WHERE facilitatorId=?""",
                           (", ".join(comps), user_msg.from_user.id))
            conn.commit()
            await bot.send_message(user_msg.from_user.id, "Ответ принят!")
        except Exception as e:
            await bot.send_message(user_msg.from_user.id, "Произошла ошибка!")
            print(e)

        # Переходим в главное меню
        state = dp.current_state(user=user_msg.from_user.id)
        await state.set_state(BotStates.START_STATE)
        await start(user_msg)


@dp.message_handler(state=BotStates.SET_UNIVERSITY_STATE)
async def set_university(msg: types.Message):
    # Получаем информацию
    university = msg.text

    try:
        # Заполняем строку в БД
        cursor.execute("""UPDATE Teams SET university=? WHERE facilitatorId=?""",
                    (university, msg.from_user.id))
        conn.commit()

        await bot.send_message(user_msg.from_user.id, "Ответ принят!")
    except Exception as e:
        # Если возникла ошибка
        await bot.send_message(msg.from_user.id, "Произошла ошибка!")
        print(e)

    # Переходим в главное меню
    state = dp.current_state(user=msg.from_user.id)
    await state.set_state(BotStates.START_STATE)
    await start(msg)


@dp.message_handler(state=BotStates.GET_SPECIALITES_SPHERE_STATE)
async def set_specialties_sphere(msg: types.Message):
    # Получаем информацию

    specs = list(filter(lambda x: x != None,
                        [i[0] for i in cursor.execute("""SELECT name
                                                      FROM Specialites WHERE sphere=?""",
                            (msg.text,)).fetchall()]))

    kb = ReplyKeyboardMarkup()
    for i in specs:
        kb.add(i)
    kb.add("Назад")

    await bot.send_message(msg.from_user.id,
                "Выберите специальность на клавиатуре снизу или введите свою:",
                reply_markup=kb)

    state = dp.current_state(user=msg.from_user.id)
    await state.set_state(BotStates.SET_SPECIALTIES_STATE)

@dp.message_handler(state=BotStates.SET_SPECIALTIES_STATE)
async def set_specialties(msg: types.Message):
    # Получаем информацию
    spec = msg.text

    if spec != "Назад":
        try:
            # Заполняем строку в БД
            cursor.execute("""UPDATE Teams SET specialties=? WHERE facilitatorId=?""",
                        (spec, msg.from_user.id))
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
    else:
        # Переходим на выбор сферы
        state = dp.current_state(user=msg.from_user.id)
        await state.set_state(BotStates.HOME_STATE)
        await start(msg) 


@dp.message_handler(state=BotStates.SET_OTHER_COMPETENCIES_STATE)
async def set_other_competencies(msg: types.Message):
    # Получаем информацию
    competencies = msg.text

    try:
        now_comps = cursor.execute("""SELECT competencies FROM Teams WHERE facilitatorId=?""",
                    (user_msg.from_user.id,)).fetchall()

        if now_comps[0][0] != "":
            competencies = ", ".join(now_comps[0][0].split(", ")) + f", {competencies}"

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

# Запуск бота
if __name__ == '__main__':
    print("Бот запущен...")
    executor.start_polling(dp, skip_updates=False)
