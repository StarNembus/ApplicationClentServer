import sys
import os
import logging.handlers
from common.variables import LOGGING_LEVEL

sys.path.append('../')

# объект форматирования, формирует логи
client_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s - %(message)s ')

# Подготовка имени файла для логирования
PATH = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(PATH, 'client.log')

# обработчик логирования
stream_handler = logging.StreamHandler(sys.stderr)
stream_handler.setFormatter(client_formatter)
stream_handler.setLevel(logging.ERROR)
log_file = logging.handlers.TimedRotatingFileHandler(PATH, encoding='utf8')
log_file.setFormatter(client_formatter)

logger = logging.getLogger('client')
logger.addHandler(stream_handler)
logger.addHandler(log_file)
logger.setLevel(LOGGING_LEVEL)


# отладка
if __name__ == '__main__':
    # потоковый обработчик логирования
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    console.setFormatter(client_formatter)
    logger.addHandler(console)
    logger.critical('Критическая ошибка')
    logger.error('Ошибка')
    logger.debug('Отладка')
    logger.info('Информационное сообщение')
