import argparse
import logging
import socket
import sys
import json
from pprint import pprint
import log.server_log_config
from decorator_log import log

from common.variables import ACTION, ACCOUNT_NAME, RESPONSE, MAX_CONNECTIONS, PRESENCE, TIME, USER, \
    ERROR, DEFAULT_PORT, RESPONDEFAULT_IP_ADDRESS
from common.utils import get_message, send_message

server_logger = logging.getLogger('server')


# pprint(sys.path)

@log
def process_client_message(message):
    """
    Обработчик сообщений от клиентов,
    принимает dict - сообщение от клиента,
    возвращает dict - ответ
    :param message:
    :return:
    """
    server_logger.debug(f'разбор сообщения от клиента: {message}')
    con1 = message[ACTION] == PRESENCE
    con2 = TIME in message
    con3 = USER in message
    con4 = message[USER][ACCOUNT_NAME] == 'Guest'
    if con1 and con2 and con3 and con4:  # обработка сообщений, сравнение ключей
        return {RESPONSE: 200}
    return {
        RESPONDEFAULT_IP_ADDRESS: 400,
        ERROR: 'Bad Request'
    }


def create_arg_parser():
    """Парсер аргументов командной строки"""
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=DEFAULT_PORT, type=int, nargs='?')
    parser.add_argument('-a', default='', nargs='?')
    return parser


def main():
    """
    Загрузка параметров командной строки, если нет параметров,
    задаются значения по умолчанию
    Обработка порта -p 8888 -a 127.0.0.1
    :return:
    """
    try:
        if '-p' in sys.argv:
            listen_port = int(sys.argv[sys.argv.index('-p') + 1])
        else:
            listen_port = DEFAULT_PORT
        if listen_port < 1024 or listen_port > 65535:
            raise ValueError
    except IndexError:
        server_logger.critical(f'Попытка запуска сервера с указанием неподходящего порта')
        sys.exit(1)
    except ValueError:
        server_logger.critical(f'{listen_port} Допустимы адреса с 1024 до 65535')
        sys.exit(1)
    server_logger.info(f'Запущен сервер, порт для подключений: {listen_port}')

    # Загрузка адреса, который будем слушать

    try:
        if '-a' in sys.argv:
            listen_address = sys.argv[sys.argv.index('-a') + 1]
        else:
            listen_address = ''

    except IndexError:
        server_logger.info(f'After \'a\' need to specify the address that the server will listen to')
        sys.exit(1)

    # Готовим сокет

    transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    transport.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,
                         1)  # для отладки, чтобы долго не ждать перезапуска сервера
    transport.bind((listen_address, listen_port))

    # Слушаем порт

    transport.listen(MAX_CONNECTIONS)  # 5 слушателей из variables.py

    while True:
        client, client_address = transport.accept()  # принимаем клиента
        server_logger.info(f'Установлено соединение{client_address}')
        try:
            message_from_client = get_message(client)  # приходит сообщение
            server_logger.debug(f'Получено сообщение {message_from_client}')
            response = process_client_message(message_from_client)  # обработка сообщения {RESPONSE: 200}
            server_logger.info(f'Сформирован ответ клиенту{response}')
            send_message(client, response)
            server_logger.debug(f'Соединение с клиентом закрывается {client_address}')
            client.close()
        except json.JSONDecodeError:
            server_logger.error(f'Не удалось декодировать строку, полученную от клиента{client_address}'
                                f'От клиента приняты некорректные данные {client_address}')
            client.close()


if __name__ == '__main__':
    main()
