import os
import json

from loguru import logger


log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)


def json_writer(message: str) -> None:
    """
    Записывает сообщения об ошибках в файл errors.json.

    Если файл `errors.json` уже существует, функция открывает его, загружает существующие логи, добавляет новое
    сообщение и сохраняет обновленный список логов обратно в файл. В случае отсутствия файла функция создает новый
    файл и записывает в него первое сообщение.

    Args:
        message (str): Сообщение об ошибке в формате JSON, которое необходимо сохранить в файл.

    Raises:
        JSONDecodeError: Если содержимое файла `errors.json` повреждено и не может быть декодировано как JSON.
    """
    log_file = os.path.join(log_dir, "errors.json")

    if os.path.exists(log_file):
        with open(log_file, "r+") as file:
            try:
                logs = json.load(file)
            except json.JSONDecodeError:
                logs = []

            logs.append(json.loads(message))
            file.seek(0)
            json.dump(logs, file, indent=4)
    else:
        with open(log_file, "w") as file:
            json.dump([json.loads(message)], file, indent=4)


def setup_logger() -> logger:
    """
    Настраивает логирование с использованием библиотеки loguru.

    Функция создает два логгера:
    1. Логгер для ошибок, сохраняющий сообщения в файл `errors.json` в директории логов.
    2. Логгер для информационных сообщений и отладочной информации, сохраняющий данные в файл `info.log`
        в той же директории.

    Логгеры настраиваются с параметрами:
        - Уровень логирования (`ERROR` для ошибок, `DEBUG` для информационных сообщений).
        - Формат сообщений.
        - Ротация логов при достижении 50 МБ.
        - Сохранение сообщений в формате JSON.
        - Включение стека вызовов (`backtrace`) и подробной диагностики (`diagnose`).

    Returns:
        logger: Настроенный объект логгера loguru.
    """
    formatting = "{time:DD.MM.YYYY в HH:mm:ss} | {level} | {module}:{function}:{line} - {message}>"

    logger.add(
        json_writer,
        format=formatting,
        serialize=True,
        level="ERROR",
        backtrace=True,
        diagnose=True,
    )

    logger.add(
        os.path.join(log_dir, "info.log"),
        format=formatting,
        level="DEBUG",
        rotation="50 MB",
        backtrace=True,
        diagnose=True,
    )

    return logger


log = setup_logger()
