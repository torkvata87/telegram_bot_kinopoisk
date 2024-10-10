from loader import bot
from telebot.apihelper import ApiTelegramException
from logs.logging_config import log
import handlers
from telebot.custom_filters import StateFilter
from utils.set_bot_commands import set_default_commands


if __name__ == "__main__":
    bot.add_custom_filter(StateFilter(bot))
    set_default_commands(bot)

    try:
        bot.infinity_polling(skip_pending=True)
    except ApiTelegramException as exc:
        if exc.result_json["error_code"] == 401:
            log.error("Неверно указан токен. Проверьте BOT_TOKEN.", exc_info=True)
        else:
            log.error(f"Ошибка при взаимодействии с Telegram API: {exc}", exc_info=True)
    except Exception as exc:
        log.error(f"Произошла непредвиденная ошибка {type(exc).__name__}: {exc}", exc_info=True)
