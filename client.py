import json
import socket
import time
import sys

from common.utils import send_message, get_message
from common.variables import ACTION, ACCOUNT_NAME, RESPONSE, PRESENCE, TIME, USER, \
    ERROR, DEFAULT_PORT, DEFAULT_IP_ADRESS


def create_presence(account_name='Guest'):
    """
    Генерирует запрос о присутствии клиента
    :param account_name:
    :return:
    """
    out = {
        ACTION: PRESENCE,
        TIME: time.time(),
        USER: {
            ACCOUNT_NAME: account_name
        }
    }

    return out


def process_ans(message):
    """
    Разбирает ответ сервера
    :param message:
    :return:
    """
    if RESPONSE in message:
        if message(RESPONSE) == 200:
            return '200: OK'
        return f'400: {message[ERROR]}'
    raise ValueError


def main():
    """Загружаем параметры командной строки"""
    try:
        server_address = sys.argv[1]
        server_port = int(sys.argv[2])
        if server_port < 1024 or server_port > 65535:
            raise ValueError
    except IndexError:
        server_address = DEFAULT_IP_ADRESS
        server_port = DEFAULT_PORT
    except ValueError:
        print('The port can only be a number between 1024 and 65535')
        sys.exit(1)

    # Инициализация сокета и обмен

    transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    transport.connect((server_address, server_port))
    message_to_server = create_presence()
    send_message(transport, message_to_server)
    try:
        answer = process_ans(get_message(transport))
        print(answer)
    except (ValueError, json.JSONDecodeError):
        print('Failed to decode server messages')


if __name__ == '__main__':
    main()
