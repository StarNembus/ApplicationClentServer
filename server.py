import socket
import sys
import json
from pprint import pprint

from common.variables import ACTION, ACCOUNT_NAME, RESPONSE, MAX_CONNECTIONS, PRESENCE, TIME, USER, \
    ERROR, DEFAULT_PORT, RESPONDEFAULT_IP_ADDRESS
from common.utils import get_message, send_message
# pprint(sys.path)

def process_client_message(message):
    """
    Обработчик сообщений от клиентов,
    принимает dict - сообщение от клиента,
    возвращает dict - ответ
    :param message:
    :return:
    """
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
        print('After -\'p\' need to specify the port number')
        sys.exit(1)
    except ValueError:
        print('The port can only be a number between 1024 and 65535')
        sys.exit(1)

    # Загрузка адреса, который будем слушать

    try:
        if '-a' in sys.argv:
            listen_address = sys.argv[sys.argv.index('-a') + 1]
        else:
            listen_address = ''

    except IndexError:
        print('After \'a\' need to specify the address that the server will listen to')
        sys.exit(1)

    # Готовим сокет

    transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    transport.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # для отладки, чтобы долго не ждать перезапуска сервера
    transport.bind((listen_address, listen_port))

    # Слушаем порт

    transport.listen(MAX_CONNECTIONS)  # 5 слушателей из variables.py

    while True:
        client, client_address = transport.accept()  # принимаем клиента
        try:
            message_from_client = get_message(client)  # приходит сообщение
            print(message_from_client)
            response = process_client_message(message_from_client)  # обработка сообщения {RESPONSE: 200}
            send_message(client, response)
            client.close()
        except (ValueError, json.JSONDecodeError):
            print('Incorrect message received from client')
            client.close()


if __name__ == '__main__':
    main()























