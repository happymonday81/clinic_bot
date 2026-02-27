import logging
import sys
from pathlib import Path


def setup_logging(
    level: int = logging.INFO,
    log_file: str = "bot.log",
    log_format: str = "%(asctime)s | %(name)s | %(levelname)-8s | %(message)s",
    date_format: str = "%Y-%m-%d %H:%M:%S"
):
    """
    Настраивает логирование для бота
    
    Args:
        level: Уровень логирования (logging.INFO, logging.DEBUG и т.д.)
        log_file: Путь к файлу лога
        log_format: Формат сообщений
        date_format: Формат даты
    """
    # Создаём директорию для логов если нет
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Конфигурация
    logging.basicConfig(
        level=level,
        format=log_format,
        datefmt=date_format,
        handlers=[
            # Вывод в консоль
            logging.StreamHandler(sys.stdout),
            # Вывод в файл с UTF-8 кодировкой
            logging.FileHandler(log_file, encoding='utf-8', mode='a')
        ]
    )
    
    # Убираем лишние логи от aiogram и других библиотек
    logging.getLogger('aiogram').setLevel(logging.WARNING)
    logging.getLogger('aiohttp').setLevel(logging.WARNING)
    
    logger = logging.getLogger(__name__)
    logger.info("🔧 Logging configured successfully")
    logger.info(f"📝 Log file: {log_path.absolute()}")
    
    return logging.getLogger('clinic_bot')


def get_logger(name: str = __name__) -> logging.Logger:
    """Получает логгер с указанным именем"""
    return logging.getLogger(name)