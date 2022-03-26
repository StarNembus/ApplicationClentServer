import argparse
import json
import socket
import threading
import time
import sys

import log.server_log_config
import logging

from common.utils import send_message, get_message
from common.variables import ACTION, ACCOUNT_NAME, RESPONSE, PRESENCE, TIME, USER, \
    ERROR, DEFAULT_PORT, DEFAULT_IP_ADRESS, MESSAGE, SENDER, MESSAGE_TEXT, DESTINATION, EXIT
from errors import ServerError, ReqFieldMissingError, IncorrectDataRecivedError
from decorator_log import log

# Инициализация клиентского логера
client_logger = logging.getLogger('client')

@log
def create_exit_message(account_name):
    """Создает словарь с сообщением о выходе"""
    return {
        ACTION: EXIT,
        TIME: time.time(),
        ACCOUNT_NAME: account_name
    }


@log
def message_from_server(sock, my_username):
    """Обработчик сообщений пользователей, поступающих с сервера"""
    while True:
        try:
            message = get_message(sock)
            if ACTION in message and message[ACTION] == MESSAGE and \
                    SENDER in message and DESTINATION in message \
                    and MESSAGE_TEXT in message and message[DESTINATION] == my_username:
                print(f'\nПолучено сообщение от пользователя {message[SENDER]}:'
                      f'\n{message[MESSAGE_TEXT]}')

                client_logger.info(f'Получено сообщение от пользователя '
                                f'{message[SENDER]}:\n{message[MESSAGE_TEXT]}')
            else:
                client_logger.error(f'Получено некорректное сообщение с сервера: {message}')
        except IncorrectDataRecivedError:
            client_logger.error(f'Не удалось декодировать полученное сообщение.')
        except (OSError, ConnectionError, ConnectionAbortedError, ConnectionResetError, json.JSONDecodeError):
            client_logger.critical(f'Нет соединения с сервером')
            break

    # if ACTION in message and message[ACTION] == MESSAGE and \
    #         SENDER in message and MESSAGE_TEXT in message:
    #     print(f'Пришло сообщение от пользователя '
    #           f'{message[SENDER]}: \n {message[MESSAGE_TEXT]}')
    #     client_logger.info(f'Получено сообщение от пользователя '
    #                        f'{message[SENDER]}:\n{message[MESSAGE_TEXT]}')
    # else:
    #     client_logger.error(f'Получено некорректное сообщение с сервера: {message}')


@log
def create_message(sock, account_name='Guest'):
    """Запрос текста сообщения"""
    to_user = input('Введите получателя сообщения: ')
    message = input('Введите сообщение или \'!!!\' для завершения работы')
    # if message == '!!!':
    #     sock.close()
    #     client_logger.info('Завершение работы по команде от пользователя')
    #     print('Выход')
    #     sys.exit(0)
    message_dict = {
        ACTION: MESSAGE,
        SENDER: account_name,
        DESTINATION: to_user,
        TIME: time.time(),
        MESSAGE_TEXT: message
    }
    client_logger.debug(f'Сформирован словарь сообщения:{message_dict}')
    try:
        send_message(sock, message_dict)
        client_logger.info(f'Отправлено сообщение для пользователя {to_user}')
    except Exception as e:
        print(e)
        client_logger.critical('Нет соединения с сервером')
        sys.exit(1)
    # return message_dict


def print_help():
    """Функция выводящяя справку по использованию"""
    print('Команды:')
    print('message - отправить сообщение. Кому, текст будут запрошены отдельно.')
    print('help - вывести подсказки')
    print('exit - выход ')


@log
def user_interactive(sock, username):
    """Взаимодействие с пользователем, запрашивает команды, отправляет сообщения"""
    print_help()
    while True:
        command = input('Введите команду: ')
        if command == 'message':
            create_message(sock, username)
        elif command == 'help':
            print_help()
        elif command == 'exit':
            send_message(sock, create_exit_message(username))
            print('Завершение соединения.')
            client_logger.info('Завершение работы по команде пользователя.')
            time.sleep(0.5)
            break
        else:
            print('Команда не распознана. help - вывести команды')


@log
def create_presence(account_name):
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
    client_logger.debug(f'Сформировано {PRESENCE} сообщение для пользователя{account_name}')

    return out

@log
def process_ans(message):
    """
    Разбирает ответ сервера
    :param message:
    :return:
    """
    client_logger.debug(f'Разбор приветственного сообщения от сервера: {message}')
    if RESPONSE in message:
        if message[RESPONSE] == 200:
            return '200 : OK'
        elif message[RESPONSE] == 400:
            raise ServerError(f'400 : {message[ERROR]}')
    raise ReqFieldMissingError(RESPONSE)


@log
def arg_parser():
    """Парсер аргументов командной строки,
    читаем параметры, возвращаем 3 параметра"""
    parser = argparse.ArgumentParser()
    parser.add_argument('addr', default=DEFAULT_IP_ADRESS, nargs='?')
    parser.add_argument('port', default=DEFAULT_PORT, type=int, nargs='?')
    parser.add_argument('-m', '--name', default='None', nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    server_address = namespace.addr
    server_port = namespace.port
    client_name = namespace.name

    # проверка подходящего порта
    if not 1023 < server_port < 65536:
        client_logger.critical(
            f'Попытка запуска клиента с неподходящим номером порта: {server_port}. '
            f'Допустимы адреса с 1024 до 65535. Клиент завершается.'
        )
        sys.exit(1)

    # проверка допустим ли выбранный режим работы клиента
    # if client_name not in ('listen', 'send'):
    #     client_logger.critical(f'Указан недопустимый режим работы {client_name}, '
    #                            f'допустимые режимы: listen , send')
    #     sys.exit(1)

    return server_address, server_port, client_name


def main():
    """Загружаем параметры командной строки"""
    server_address, server_port, client_name = arg_parser()

    """Сообщаем о запуске"""
    print(f'Консольный месседжер. Клиентский модуль. Имя пользователя: {client_name}')

    # Если имя пользователя не было задано, необходимо запросить пользователя
    if not client_name:
        client_name = input('Введите имя пользователя: ')

    client_logger.info(
        f'Запущен клиент с парамертами: адрес сервера: {server_address}, '
        f'порт: {server_port}, режим работы: {client_name}'
    )

    # Инициализация сокета и сообщение серверу о нашем появлении
    try:
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.connect((server_address, server_port))
        send_message(transport, create_presence())
        answer = process_ans(get_message(transport))
        client_logger.info(f'Установлено соединение с сервером. Ответ сервера: {answer}')
        print(f'Установлено соединение с сервером.')
    except json.JSONDecodeError:
        client_logger.error('Не удалось декодировать полученную Json строку.')
        sys.exit(1)
    except ServerError as error:
        client_logger.error(f'При установке соединения сервер вернул ошибку: {error.text}')
        sys.exit(1)
    except ReqFieldMissingError as missing_error:
        client_logger.error(f'В ответе сервера отсутствует необходимое поле {missing_error.missing_field}')
        sys.exit(1)
    except (ConnectionRefusedError, ConnectionError):
        client_logger.critical(
            f'Не удалось подключиться к серверу {server_address}:{server_port}, '
            f'конечный компьютер отверг запрос на подключение.'
        )
        sys.exit(1)
    else:
        """Если соединение с сервером установлено корректно,
        запускаем клиентский процесс приёма сообщений"""
        receiver = threading.Thread(target=message_from_server, args=(transport, client_name))
        receiver.daemon = True
        receiver.start()

        # затем запускаем отправку сообщений и взаимодействие с пользователем.
        user_interface = threading.Thread(target=user_interactive, args=(transport, client_name))
        user_interface.daemon = True
        user_interface.start()
        client_logger.debug('Запущены процессы')

        # Watchdog основной цикл, если один из потоков завершён,
        # то значит или потеряно соединение или пользователь
        # ввёл exit. Поскольку все события обработываются в потоках,
        # достаточно просто завершить цикл.

        while True:
            time.sleep(1)
            if receiver.is_alive() and user_interface.is_alive():
                continue
            break

        # if client_mode == 'send':
        #     print('Режим работы - отправка сообщений.')
        # else:
        #     print('Режим работы - приём сообщений.')
        # while True:
        #     # режим работы - отправка сообщений
        #     if client_mode == 'send':
        #         try:
        #             send_message(transport, create_message(transport))
        #         except (ConnectionResetError, ConnectionError, ConnectionAbortedError):
        #             client_logger.error(f'Соединение с сервером {server_address} было потеряно.')
        #             sys.exit(1)
        #     # режим работы приём:
        #     if client_mode == 'listen':
        #         try:
        #             message_from_server(get_message(transport))
        #         except (ConnectionResetError, ConnectionError, ConnectionAbortedError):
        #             client_logger.error(f'Соединение с сервером {server_address} было потеряно.')
        #             sys.exit(1)

if __name__ == '__main__':
    main()
