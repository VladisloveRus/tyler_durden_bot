import webbrowser
import telebot
import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()
bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))  # type: ignore
tg_id_set = set()


@bot.message_handler(commands=["create_DB"])
def create_db(message):
    """Функция создания базы данных пользователей"""
    conn = sqlite3.connect("tyler_durden_database.sql")
    cur = conn.cursor()
    cur.execute(
        "CREATE TABLE IF NOT EXISTS users (id integer primary key autoincrement, tg_id integer not null unique, name varchar(50))"
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


#        print(
#            f"tg_id_list = {tg_id_list} : {type(tg_id_list)} , tg_id = {tg_id} : {type(tg_id)}, tg_id_set = {tg_id_set} : {type(tg_id_set)}"
#        )


def check_user(message):
    """Идентификация зарегистрированного пользователя"""
    if message.chat.id not in tg_id_set:
        print(message.chat.id, tg_id_set)
        bot.reply_to(message, "Привет. Мы не знакомы, представься.")
        bot.register_next_step_handler(message, register_user)
    else:
        conn = sqlite3.connect("tyler_durden_database.sql")
        cur = conn.cursor()
        db_name = cur.execute(
            "SELECT name FROM users WHERE tg_id = ('%i') LIMIT 1"
            % (message.chat.id)
        )
        name = db_name.fetchone()[0]
        bot.reply_to(message, f"Привет, {name}")


@bot.message_handler(commands=["reg"])
def register_user(message):
    name = message.text.strip()
    tg_id = message.chat.id
    conn = sqlite3.connect("tyler_durden_database.sql")
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO users (name, tg_id) VALUES ('%s', '%i')"
            % (name, tg_id)
        )
    except sqlite3.IntegrityError:
        bot.send_message(
            message.chat.id,
            f"Что-то пошло не так. Напиши по этому поводу {os.getenv("CREATOR")}, он разберётся.",
        )
    else:
        conn.commit()
        update_tg_id_set()
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton(
                "Список пользователей", callback_data="users"
            ),
            telebot.types.InlineKeyboardButton(
                "Список telegram id", callback_data="tg_id_set"
            ),
        )
        bot.send_message(
            message.chat.id,
            "Хорошо. Я - Тайлер Дёрден.",
            reply_markup=markup,
        )
    finally:
        cur.close()
        conn.close()


@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    conn = sqlite3.connect("tyler_durden_database.sql")
    cur = conn.cursor()
    if call.data == "users":
        cur.execute("SELECT * FROM users")
        user_list = cur.fetchall()
        info = ""
        for unit in user_list:
            info += f"Имя: {unit[2]}, Telegram id: {unit[1]}"
        bot.send_message(call.message.chat.id, info)
    cur.close()
    conn.close()
    if call.data == "tg_id_set":
        bot.send_message(call.message.chat.id, str(tg_id_set))


#    bot.reply_to(
#        message,
#        f"Значит, тебя зовут {name}? Хорошо. Я - Тайлер. Тайлер Дёрден.",
#    )


@bot.message_handler(commands=["start", "hello"])
def start(message):
    create_db(message)
    update_tg_id_set()
    check_user(message)


#    markup = telebot.types.InlineKeyboardMarkup()
#    markup.add(
#        telebot.types.InlineKeyboardButton(
#            "Подписаться на канал", url=os.getenv("INVITE")
#        )
#    )
#    bot.send_message(
#        message.chat.id,
#        "Привет, я - <b>Тайлер Дёрден</b>",
#        parse_mode="html",
#        reply_markup=markup,
#    )


@bot.message_handler(commands=["link"])
def link(message):
    bot.send_message(message.chat.id, "Добро пожаловать.")
    webbrowser.open(os.getenv("INVITE"))


@bot.message_handler(content_types=["photo", "video"])
def get_photo(message):
    bot.reply_to(message, "Я не буду это смотреть.")


@bot.message_handler(content_types=["audio"])
def get_audio(message):
    bot.reply_to(message, "Я не буду это слушать.")


@bot.message_handler()
def messaging(message):
    if message.text == "Покажи мне всё":
        bot.send_message(message.chat.id, message)
    else:
        bot.reply_to(message, "Что?")


bot.infinity_polling()
