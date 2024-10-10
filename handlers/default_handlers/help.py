from telebot.types import Message

from config_data.config import IMAGE_HELP
from loader import bot

from database.core import crud_images

from services.services_logging import error_logger_bot

from logs.logging_config import log


@bot.message_handler(commands=["help"])
@error_logger_bot
def menu_help(message: Message) -> None:
    """
    Обработчик команды /help.

    Действия:
        - Выполняет сброс состояния и всех данных, связанных с текущей сессией пользователя.
        - Сохраняет изображение для команды `help` в базе данных ImageFile для быстрого к нему доступа
        при повторном использовании.
        - Отправляет в чат сообщение с изображением и перечнем существующих команд.

    Args:
        message (Message): Объект, содержащий данные сообщения от пользователя.
            - message.text (str): Текст сообщения с командой `help`.
    """
    user_id, chat_id = message.from_user.id, message.chat.id
    bot.reset_data(user_id, chat_id)

    db_get_image = crud_images.get_image()
    db_save = crud_images.save_image()

    image_name = "help"
    file_id = db_get_image(chat_id, image_name)
    caption = (
        f"❓<b>Справка по использованию бота</b>\n\n"
        f"<i>{message.chat.first_name}</i>, вот мои основные <b><i>команды</i></b> 📋:\n\n"
        "🚀 /start — <i>Запустить бота</i>\n\n"
        "🔍 /movie_search — <i>Поиск фильма по названию</i>\n\n"
        "🔍 /movie_by_filters — <i>Поиск фильмов/сериалов по фильтрам</i>\n\n"
        "📌 /postponed_movies — <i>Просмотр избранных и просмотренных фильмов</i>\n\n"
        "📚 /history — <i>Управление историей поисковых запросов</i>\n\n"
        "📩 <i>torkvata87@gmail.com</i> -  <i>Обратиться в службу поддержки</i> телеграм-бота"
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
            with open(IMAGE_HELP, "rb") as image:
                sent_message = bot.send_photo(
                    chat_id,
                    image,
                    caption=caption,
                    parse_mode="HTML",
                )
                db_save(chat_id, image_name, sent_message.photo[-1].file_id)
    except FileNotFoundError as exc:
        log.error(f"Ошибка при обработке изображения: {type(exc).__name__} - {exc}.")
        log.info(f"Пользователю отправлено сообщение без картинки.")
        bot.send_message(chat_id, caption, parse_mode="HTML")
