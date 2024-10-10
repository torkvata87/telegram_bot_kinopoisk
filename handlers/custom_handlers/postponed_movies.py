from telebot.types import Message, CallbackQuery

from config_data.config import IMAGE_POSTPONED_MOVIES
from loader import bot

from services.services_utils import set_ids
from services.services_database import sending_to_pagination
from services.services_pagination_handlers import send_movie_pagination
from services.services_logging import error_logger_bot
from services.services_postponed_movies import data_postponed

from logs.logging_config import log

from states.search_fields import PostponedStates

from database.core import crud_images
from database.common.models_movies import MoviePostponed

from keyboards.buttons.btns_for_postponed_movies import buttons_postponed
from keyboards.inline.inline_keyboard import create_inline_keyboard


@bot.message_handler(commands=["postponed_movies"])
@bot.callback_query_handler(func=lambda call: call.data == "postponed_movies")
@error_logger_bot
def menu_postponed_movies(message_or_call: Message | CallbackQuery) -> None:
    """
    Обработчик команды /postponed_movies и нажатия на кнопку `postponed_movies`.

    Действия:
        - Выполняет сброс состояния и всех данных, связанных с текущей сессией пользователя.
        - Устанавливает состояние пользователя `PostponedStates.postponed`.
        - Сохраняет изображение для команды `postponed_movies` в базе данных ImageFile для быстрого
        к нему доступа при повторном использовании.
        - Проверяет наличие отложенных фильмов в базе данных MoviesPostponed.
        - Отправляет в чат сообщение с изображением и сообщение с инлайн-клавиатурой отложенных фильмов,
        если они присутствуют в базе данных.
        - Удаляет сообщение, вызвавшее запрос при нажатии на кнопку `postponed_movies`.

    Args:
        message_or_call (Message | CallbackQuery): Объект, содержащий данные сообщения или callback-запроса.
        Если это `Message`:
            - message.text (str): Текст сообщения с командой `postponed_movies`.
        Если это `CallbackQuery`:
            - call.data (str): Название кнопки `postponed_movies`.
    """
    chat_id, user_id, message_id = set_ids(message_or_call)

    bot.reset_data(user_id, chat_id)
    bot.set_state(user_id, PostponedStates.postponed, chat_id)

    if isinstance(message_or_call, Message):
        db_get_image = crud_images.get_image()
        db_save = crud_images.save_image()

        image_name = "postponed_movies"
        file_id = db_get_image(chat_id, image_name)
        caption = "📌 <b>Ваши избранные и просмотренные фильмы.</b>"
        try:
            if file_id:
                bot.send_photo(
                    chat_id,
                    file_id,
                    caption=caption,
                    parse_mode="HTML",
                )
            else:
                with open(IMAGE_POSTPONED_MOVIES, "rb") as image:
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

    user_movies = MoviePostponed.select().where(MoviePostponed.user_id == user_id)
    if not user_movies.exists():
        text = (
            "❎ Сейчас у вас нет <b><i>избранных</i></b> и <b><i>просмотренных</i></b> фильмов.\n\n"
            "✅ Добавляйте фильмы в просмотренные или в избранные и просматривайте их здесь ☺️."
        )
        keyboard = None
    else:
        has_favorites = user_movies.where(MoviePostponed.is_favorites).exists()
        has_viewed = user_movies.where(MoviePostponed.is_viewed).exists()

        btns = {}
        if has_favorites:
            btns["favorites"] = buttons_postponed["favorites"]
        if has_viewed:
            btns["viewed"] = buttons_postponed["viewed"]

        keyboard = create_inline_keyboard(btns, buttons_per_row=1)

        with bot.retrieve_data(user_id, chat_id) as data:
            data.clear()
            data["buttons_postponed"] = btns

        text = (
            "Здесь вы можете посмотреть <b><i>фильмы/сериалы</i></b>, которые вы пометили как "
            "🌟 <b><i>избранное</i></b> или \n✅ <b><i>просмотренное</i></b>."
        )

    bot.send_message(chat_id, text, reply_markup=keyboard, parse_mode="HTML")

    if isinstance(message_or_call, CallbackQuery):
        bot.delete_message(chat_id, message_id)


@bot.callback_query_handler(func=lambda call: call.data in list(buttons_postponed))
@error_logger_bot
def select_postponed(call: CallbackQuery) -> None:
    """
    Обработчик нажатий на кнопки для вызова отображения просмотренных или избранных фильмов.

    Действия:
        - Устанавливает состояние пользователя `PostponedStates.favorite` либо `PostponedStates.viewed`.
        - На основе полученных результатов из базы данных MoviesPostponed формирует словарь просмотренных
        или избранных фильмов.
        - Выводит перечень просмотренных или избранных фильмов в виде пагинации.
        - Удаляет сообщение, вызвавшее запрос.

    Args:
        call (CallbackQuery): Объект, содержащий информацию о нажатой кнопке.
            - call.data (str): Название выбранной категории отложенного фильма из их перечня.
    """
    user_id, chat_id = call.from_user.id, call.message.chat.id
    bot.reset_data(user_id, chat_id)

    states, status_base, status = data_postponed(call.data)

    user_movies = (
        MoviePostponed.select()
        .where((MoviePostponed.user_id == user_id) & status_base)
        .order_by(MoviePostponed.id.desc())
    )

    bot.set_state(user_id, states, chat_id)

    with bot.retrieve_data(user_id, chat_id) as data:
        data["movie_info"] = sending_to_pagination(
            user_movies, type_search="postponed_movies"
        )
        data["button_postponed"] = status
    send_movie_pagination(chat_id, data["movie_info"], total_pages=1)
    bot.delete_message(chat_id, call.message.message_id)
