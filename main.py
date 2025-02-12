import sqlite3
import telebot
import webbrowser
from dotenv import load_dotenv
import os

load_dotenv()
bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))  # type: ignore
tg_id_set = set()


@bot.message_handler(commands=["create_DB"])
def create_db(message):
    """Функция создания базы данных пользователей"""
    conn = sqlite3.connect("tyler_durden_database.sql")
    cur = conn.cursor()
    cur.execute(
        "CREATE TABLE IF NOT EXISTS users (id integer primary key autoincrement, tg_id integer, name varchar(50))"
    )
    conn.commit()
    cur.close()
    conn.close()
    bot.reply_to(message, "Да записываю я, записываю!")


def update_tg_id_set():
    """Обновление глобального множества tg_id_set для идентификации зарегистрированных пользователей"""
    global tg_id_set
    conn = sqlite3.connect("tyler_durden_database.sql")
    cur = conn.cursor()
    cur.execute("SELECT tg_id FROM users")
    tg_id_list = cur.fetchall()
    cur.close()
    conn.close()
    for tg_id in tg_id_list[0]:
        tg_id_set.add(tg_id)


def check_user(message):
    """Идентификация зарегистрированного пользователя"""
    if message.chat.id not in tg_id_set:
        bot.reply_to(message, "Привет. Мы не знакомы, представься.")
        bot.register_next_step_handler(message, register_user)
    else:
        conn = sqlite3.connect("tyler_durden_database.sql")
        cur = conn.cursor()
        db_name = cur.execute(
            "SELECT name FROM users WHERE tg_id = ? LIMIT 1",
            (message.chat.id,),
        )
        name = db_name.fetchone()[0]
        bot.reply_to(message, f"Привет, {name}")


@bot.message_handler(commands=["reg"])
def register_user(message):
    """Функция регистрации нового пользователя"""
    name = message.text.strip()
    tg_id = message.chat.id
    conn = sqlite3.connect("tyler_durden_database.sql")
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO users (tg_id, name) VALUES (?, ?)", (tg_id, name)
        )
    except sqlite3.IntegrityError:
        bot.send_message(
            message.chat.id,
            f"Что-то пошло не так. Напиши по этому поводу {os.getenv('CREATOR')}, он разберётся.",
        )
    else:
        conn.commit()
        update_tg_id_set()
        # Начало временного функционала
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton(
                "Список пользователей", callback_data="users"
            ),
            telebot.types.InlineKeyboardButton(
                "Список telegram id", callback_data="tg_id_set"
            ),
        )
        # Конец временного функционала
        bot.send_message(
            message.chat.id,
            "Хорошо. Я - Тайлер Дёрден.",
            reply_markup=markup,  # Элемент временного функционала
        )
    finally:
        cur.close()
        conn.close()


@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    """Функционал кнопок"""
    conn = sqlite3.connect("tyler_durden_database.sql")
    cur = conn.cursor()
    if call.data == "users":
        """Коллбэк, отвечающий за вызов списка пользователей"""
        cur.execute("SELECT * FROM users")
        user_list = cur.fetchall()
        info = ""
        for unit in user_list:
            info += f"Имя: {unit[2]}, Telegram id: {unit[1]}"
        bot.send_message(call.message.chat.id, info)
    cur.close()
    conn.close()
    if call.data == "tg_id_set":
        """Коллбэк, отвечающий за вызов множества tg_id_set"""
        bot.send_message(call.message.chat.id, str(tg_id_set))


@bot.message_handler(commands=["start", "hello"])
def start(message):
    """Обработка стартовых сообщений"""
    # Тестовый функционал
    create_db(message)
    update_tg_id_set()
    check_user(message)


@bot.message_handler(commands=["link"])
def link(message):
    """Функция получения ссылки-приглашения"""
    bot.send_message(message.chat.id, "Добро пожаловать в клуб.")
    webbrowser.open(os.getenv("INVITE"))  # type: ignore


@bot.message_handler(content_types=["photo", "video"])
def get_photo(message):
    """Реакция бота на фото и видео"""
    bot.reply_to(message, "Я не буду это смотреть.")


@bot.message_handler(content_types=["audio"])
def get_audio(message):
    """Реакция бота на аудио"""
    bot.reply_to(message, "Я не буду это слушать.")


@bot.message_handler()
def messaging(message):
    """Реакция на другие сообщения"""
    # Тестовый функционал
    if message.text == "Покажи мне всё":
        bot.send_message(message.chat.id, message)
    else:
        bot.reply_to(message, "Что?")


bot.infinity_polling()
