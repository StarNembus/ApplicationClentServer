"""
Создание именованного логгера;
Сообщения лога должны иметь следующий формат: "<дата-время> <уровень_важности> <имя_модуля> <сообщение>";
Журналирование должно производиться в лог-файл;
На стороне сервера необходимо настроить ежедневную ротацию лог-файлов.
"""
import logging
import os.path
import sys
import logging.handlers
from common.variables import LOGGING_LEVEL
sys.path.append('../')

# объект форматирования, формирует логи
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s - %(message)s ')

# Подготовка имени файла для логирования
PATH = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(PATH, 'server.log')

# обработчик логирования
stream_handler = logging.StreamHandler(sys.stderr)
stream_handler.setFormatter(formatter)
stream_handler.setLevel(logging.ERROR)
log_file = logging.handlers.TimedRotatingFileHandler(PATH, encoding='utf8', interval=1, when='D')
log_file.setFormatter(formatter)

# Добавляем в логгер новый обработчик событий и устанавливаем уровень логирования
# объект-логгер
logger = logging.getLogger('server')
logger.addHandler(stream_handler)
logger.addHandler(log_file)
logger.setLevel(LOGGING_LEVEL)


if __name__ == '__main__':
    # потоковый обработчик логирования
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    console.setFormatter(formatter)
    logger.addHandler(console)
    logger.critical('Критическая ошибка')
    logger.error('Ошибка')
    logger.debug('Отладка')
    logger.info('Информационное сообщение')