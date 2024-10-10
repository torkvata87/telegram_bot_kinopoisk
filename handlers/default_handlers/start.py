from telebot.types import Message

from config_data.config import IMAGE_START
from database.core import crud_images
from loader import bot
from states.search_fields import StartStates

from services.services_logging import error_logger_bot
from logs.logging_config import log


@bot.message_handler(commands=["start"])
@error_logger_bot
def menu_start(message: Message) -> None:
    """
    Обработчик команды /start.

    Действия:
    - Сбрасывает состояние и все данные, связанные с текущей сессией пользователя.
    - Устанавливает состояние пользователя в `StartStates.start`.
    - Извлекает изображение для команды `start` из базы данных ImageFile.
    - Отправляет изображение и приветственное сообщение в чат.

    Args:
        message (Message): Объект, содержащий данные сообщения от пользователя.
            - message.text (str): Текст сообщения с командой `start`.

    Raises:
        FileNotFoundError: Если файл изображения не найден, отправляется сообщение с ошибкой.
    """
    user_id, chat_id = message.from_user.id, message.chat.id
    bot.reset_data(user_id, chat_id)
    bot.set_state(user_id, StartStates.start, chat_id)

    db_get_image = crud_images.get_image()
    db_save = crud_images.save_image()

    image_name = "start"
    file_id = db_get_image(chat_id, image_name)
    caption = (
        f"🚀 Рад приветствовать вас, <i>{message.chat.first_name}</i> 👋!\n\n"
        "🦔 Я - <b>бот-поисковик</b> фильмов с базой данных 🌐 "
        '<i><a href="http://www.kinopoisk.ru/">Кинопоиск</a></i>.\n\n'
        "🔍 Здесь вы можете искать фильмы и сериалы на свой вкус и просматривать их описание 📜.\n\n"
        "❓ Информацию об основных моих командах можно получить в /help."
    )
    try:
        if file_id:
            bot.send_photo(
                chat_id,
                file_id,
                caption=caption,
                parse_mode="HTML",
            )
        else:
            with open(IMAGE_START, "rb") as image:
                sent_message = bot.send_photo(
                    chat_id,
                    image,
                    caption=caption,
                    parse_mode="HTML",
                )
                db_save(chat_id, image_name, sent_message.photo[-1].file_id)
    except FileNotFoundError as exc:
        log.error(f"Ошибка при обработке изображения: {type(exc)} - {exc}")
        bot.send_message(chat_id, caption, parse_mode="HTML")


@bot.message_handler(
    state=StartStates.start, func=lambda message: not message.text.startswith("/")
)
@error_logger_bot
def list_commands(message: Message) -> None:
    """
    Обработчик сообщений, не являющихся командами, в состоянии `StartStates.start`.

    Действия:
        - Отправляет в чат сообщение с перечнем существующих команд.

    Args:
        message (Message): Объект, содержащий данные сообщения от пользователя.
            - message.text (str): Текст сообщения, не являющегося командой.
    """
    text = (
        f"<i>{message.chat.first_name}</i>, вот мои основные <b><i>команды</i></b> 📋:\n\n"
        "🚀 /start — <i>Запустить бота</i>\n\n"
        "🔍 /movie_search — <i>Поиск фильма по названию</i>\n\n"
        "🔍 /movie_by_filters — <i>Поиск фильмов/сериалов по фильтрам</i>\n\n"
        "📌 /postponed_movies — <i>Просмотр избранных и просмотренных фильмов</i>\n\n"
        "📚 /history — <i>Управление историей поисковых запросов</i>\n\n"
        "❓ /help — <i>Справка по использованию бота\n\n"
        "📩 <i>torkvata87@gmail.com</i> -  <i>Обратиться в службу поддержки</i> телеграм-бота"
    )
    chat_id = message.chat.id
    bot.send_message(chat_id, text, parse_mode="HTML")
    bot.delete_message(chat_id, message.message_id)


@bot.message_handler(func=lambda message: not message.text.startswith("/"))
def handler_any_text(message: Message) -> None:
    """
    Обработчик ввода любого сообщения, если текст не является командой.

    Действия:
        - Отправляет в чат сообщение с уведомлением о том, что строка ввода неактивна.

    Args:
        message (Message): Объект, содержащий данные сообщения от пользователя.
            - message.text (str): Текст сообщения, не являющегося командой.
    """
    chat_id = message.chat.id
    text = (
        "✍️❌ <b>Сейчас строка ввода <i>не активна</i></b>.\n\nПопробуйте задать команду "
        "другим способом либо обратитесь в <b><i>меню</i></b> или /help."
    )
    bot.send_message(chat_id, text, parse_mode="HTML")
    bot.delete_message(chat_id, message.message_id)
