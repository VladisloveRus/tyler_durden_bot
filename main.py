import telebot
import webbrowser
from dotenv import load_dotenv
import os
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import SQLAlchemyError

load_dotenv()
bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))  # type: ignore
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)  # type: ignore
Base = declarative_base()
Session = sessionmaker(bind=engine)
session = Session()
tg_id_set = set()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    tg_id = Column(Integer, unique=True)
    name = Column(String(50))

    def __repr__(self):
        return f"<User(name={self.name}, tg_id={self.tg_id})>"


Base.metadata.create_all(engine)


def update_tg_id_set():
    """Обновление глобального множества tg_id_set для идентификации зарегистрированных пользователей"""
    global tg_id_set
    try:
        users = session.query(User).all()
        tg_id_set = {user.tg_id for user in users}
    except SQLAlchemyError as e:
        print(f"Ошибка при обновлении tg_id_set: {e}")


def check_user(message):
    """Идентификация зарегистрированного пользователя"""
    if message.chat.id not in tg_id_set:
        answer = bot.reply_to(
            message, "Привет. Мы не знакомы, представься. Только имя."
        )
        bot.register_next_step_handler(answer, register_user)
    else:
        try:
            user = (
                session.query(User).filter_by(tg_id=message.chat.id).first()
            )
            if user:
                bot.reply_to(message, f"Привет, {user.name}")
        except SQLAlchemyError as e:
            print(f"Ошибка при проверке пользователя: {e}")


@bot.message_handler(commands=["reg"])
def register_user(message):
    """Регистрация нового пользователя"""
    name = message.text.strip()
    tg_id = message.chat.id
    existing_user = session.query(User).filter_by(tg_id=tg_id).first()
    try:
        if existing_user:
            bot.send_message(
                message.chat.id,
                f"Что-то пошло не так. Напиши по этому поводу {os.getenv('CREATOR')}, он разберётся.",
            )
        else:
            new_user = User(tg_id=tg_id, name=name)
            session.add(new_user)
            session.commit()
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
    except SQLAlchemyError as e:
        print(f"Ошибка при регистрации пользователя: {e}")


@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    """Функционал кнопок"""
    try:
        if call.data == "users":
            """Коллбэк, отвечающий за вызов списка пользователей"""
            users = session.query(User).all()
            info = "\n".join(
                [
                    f"Имя: {user.name}, Telegram ID: {user.tg_id}"
                    for user in users
                ]
            )
            bot.send_message(call.message.chat.id, info)
        elif call.data == "tg_id_set":
            """Коллбэк, отвечающий за вызов множества tg_id_set"""
            bot.send_message(call.message.chat.id, str(tg_id_set))
    except SQLAlchemyError as e:
        print(f"Ошибка при обработке коллбэка: {e}")


@bot.message_handler(commands=["start", "hello"])
def start(message):
    """Обработка стартовых сообщений"""
    # Тестовый функционал
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
