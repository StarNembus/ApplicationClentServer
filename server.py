import argparse
import logging
import select
import socket
import sys
import json
import time

import log.server_log_config
from decorator_log import log

from common.variables import ACTION, ACCOUNT_NAME, RESPONSE, MAX_CONNECTIONS, PRESENCE, TIME, USER, \
    ERROR, DEFAULT_PORT, RESPONDEFAULT_IP_ADDRESS, MESSAGE, MESSAGE_TEXT, SENDER, RESPONSE_400, DESTINATION, EXIT
from common.utils import get_message, send_message

server_logger = logging.getLogger('server')


# pprint(sys.path)

@log
def process_client_message(message, messages_list, client, clients, names):
    """
    Обработчик сообщений от клиентов,
    принимает dict - сообщение от клиента,
    возвращает dict - ответ
    :param client:
    :param clients:
    :param names:
    :param messages_list:
    :param message:
    :return:
    """
    server_logger.debug(f'разбор сообщения от клиента: {message}')
    # Если это сообщение о присутствии, принимаем и отвечаем, усли успешно
    if ACTION in message and message[ACTION] == PRESENCE and TIME in message \
            and USER in message:
        # Если такой пользователь ещё не зарегистрирован,
        # регистрируем, иначе отправляем ответ и завершаем соединение.
        if message[USER][ACCOUNT_NAME] not in names.keys():
            names[message[USER][ACCOUNT_NAME]] = client
            send_message(client, {RESPONSE: 200})
        else:
            response = RESPONSE_400
            response[ERROR] = 'Имя пользователя уже занято.'
            send_message(client, response)
            clients.remove(client)
            client.close()
        return
    # Если это сообщение, то добавляем его в очередь сообщений. Ответ не требуется.
    elif ACTION in message and message[ACTION] == MESSAGE and \
            DESTINATION in message and TIME in message and SENDER in message and MESSAGE_TEXT in message:
        messages_list.append(message)
        return
    # Если клиент выходит
    elif ACTION in message and message[ACTION] == EXIT and ACCOUNT_NAME in message:
        clients.remove(names[message[ACCOUNT_NAME]])
        names[message[ACCOUNT_NAME]].close()
        del names[message[ACCOUNT_NAME]]
        return
    # Иначе отдаём Bad request
    else:
        response = RESPONSE_400
        response[ERROR] = 'Запрос некорректен.'
        send_message(client, response)
        return

@log
def process_message(message, names, listen_socks):
    """
    Функция адресной отправки сообщения определённому клиенту. Принимает словарь сообщение,
    список зарегистрированых пользователей и слушающие сокеты. Ничего не возвращает.
    :param message:
    :param names:
    :param listen_socks:
    :return:
    """
    if message[DESTINATION] in names and names[message[DESTINATION]] in listen_socks:
        send_message(names[message[DESTINATION]], message)
        server_logger.info(f'Отправлено сообщение пользователю {message[DESTINATION]} '
                           f'от пользователя {message[SENDER]}.')
    elif message[DESTINATION] in names and names[message[DESTINATION]] not in listen_socks:
        raise ConnectionError
    else:
        server_logger.error(f'Пользователь {message[DESTINATION]} не зарегистрирован на сервере, '
                            f'отправка сообщения невозможна.')


@log
def create_arg_parser():
    """Парсер аргументов командной строки"""
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=DEFAULT_PORT, type=int, nargs='?')
    parser.add_argument('-a', default='', nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    listen_address = namespace.a
    listen_port = namespace.p

    # проверка получения корретного номера порта для работы сервера.
    if not 1023 < listen_port < 65536:
        server_logger.critical(
            f'Попытка запуска сервера с указанием неподходящего порта '
            f'{listen_port}. Допустимы адреса с 1024 до 65535.'
        )
        sys.exit(1)
    return listen_address, listen_port

@log
def main():
    """
    Загрузка параметров командной строки, если нет параметров,
    задаются значения по умолчанию
    :return:
    """
    listen_address, listen_port = create_arg_parser()
    server_logger.info(
        f'Запущен сервер, порт для подключений: {listen_port}, '
        f'Адрес приема подключения: {listen_address}. '
        f'Если адрес не указан, принимаются соединения с любых адресов.'
    )
    transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    transport.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    transport.bind((listen_address, listen_port))
    transport.settimeout(0.5)
    # список клиентов , очередь сообщений
    clients = []
    messages = []

    # Словарь, содержащий имена пользователей и соответствующие им сокеты.
    names = dict()  # {client_name: client_socket}

    # Слушаем порт
    transport.listen(MAX_CONNECTIONS)  # 5 слушателей из variables.py
    # Основной цикл программы сервера
    while True:
        # Ждём подключения, если таймаут вышел, ловим исключение.
        try:
            client, client_address = transport.accept()  # принимаем клиента
        except OSError:
            pass
        else:
            server_logger.info(f'Установлено соединение{client_address}')
            clients.append(client)

        recv_data_list = []
        send_data_list = []
        err_lst = []
        # Проверяем на наличие ждущих клиентов
        try:
            if clients:
                recv_data_list, send_data_list, err_lst = select.select(clients, clients, [], 0)
        except OSError:
            pass
        # принимаем сообщения и если там есть сообщения,
        # кладём в словарь, если ошибка, исключаем клиента.
        if recv_data_list:
            for client_with_message in recv_data_list:
                try:
                    process_client_message(get_message(client_with_message),
                                           messages, client_with_message, clients, names)
                except Exception:
                    server_logger.info(f'Клиент {client_with_message.getpeername()} '
                                       f'отключился от сервера.')
                    clients.remove(client_with_message)
        # Если есть сообщения, обрабатываем каждое.
        for i in messages:
            try:
                process_message(i, names, send_data_list)
            except Exception:
                server_logger.info(f'Связь с клиентом с именем {i[DESTINATION]} была потеряна')
                clients.remove(names[i[DESTINATION]])
                del names[i[DESTINATION]]
        messages.clear()

        # if messages and send_data_list:
        #     message = {
        #         ACTION: MESSAGE,
        #         SENDER: messages[0][0],
        #         TIME: time.time(),
        #         MESSAGE_TEXT: messages[0][1]
        #     }
        #     del messages[0]
        #     for waiting_client in send_data_list:
        #         try:
        #             send_message(waiting_client, message)
        #         except:
        #             server_logger.info(f'Клиент {waiting_client.getpeername()} отключился от сервера.')
        #             waiting_client.close()
        #             clients.remove(waiting_client)


if __name__ == '__main__':
    main()
