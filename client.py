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
    ERROR, DEFAULT_PORT, DEFAULT_IP_ADRESS, MESSAGE, SENDER, MESSAGE_TEXT, DESTINATION, EXIT, GET_CONTACTS, LIST_INFO, \
    ADD_CONTACT, USERS_REQUEST, REMOVE_CONTACT
from errors import ServerError, ReqFieldMissingError, IncorrectDataRecivedError
from decorator_log import log

# Инициализация клиентского логера
from metaclasses import ClientMaker
from client_database import ClientDatabase

client_logger = logging.getLogger('client')

sock_lock = threading.Lock()
database_lock = threading.Lock()


class ClientSender(threading.Thread, metaclass=ClientMaker):
    def __init__(self, account_name, sock, database):
        self.account_name = account_name
        self.sock = sock
        self.database = database
        super().__init__()

    def create_exit_message(self):
        """Создает словарь с сообщением о выходе"""
        return {
            ACTION: EXIT,
            TIME: time.time(),
            ACCOUNT_NAME: self.account_name
        }

    def create_message(self):
        """Запрос текста сообщения"""
        to_user = input('Введите получателя сообщения: ')
        message = input('Введите сообщение для отправки: ')

        # проверка существования получателя
        with database_lock:
            if not self.database.check_user(to_user):
                client_logger.info(f'Попытка отправить сообщение незарегистрированому получателю: {to_user}')

        message_dict = {
            ACTION: MESSAGE,
            SENDER: self.account_name,
            DESTINATION: to_user,
            TIME: time.time(),
            MESSAGE_TEXT: message
        }
        client_logger.debug(f'Сформирован словарь сообщения:{message_dict}')

        # Сохраняем сообщения для истории
        with database_lock:
            self.database.save_message(self.account_name, to_user, message)

        with sock_lock:
            try:
                send_message(self.sock, message_dict)
                client_logger.info(f'Отправлено сообщение для пользователя {to_user}')
            except OSError as err:
                if err.errno:
                    client_logger.critical('Нет соединения с сервером')
                    exit(1)
            else:
                client_logger.error('Не удалось передать сообщение. Таймаут соединения')

    def run(self):
        """
        Функция взаимодействия с пользователем, запрашивает команды, отправляет сообщения
        :return:
        """
        self.print_help()
        while True:
            command = input('Введите команду: ')
            if command == 'message':
                self.create_message()
            elif command == 'help':
                self.print_help()
            elif command == 'exit':
                with sock_lock:
                    try:
                        send_message(self.sock, self.create_exit_message())
                    except Exception as e:
                        print(e)
                        pass
                    print('Завершение соединения.')
                    client_logger.info('Завершение работы по команде пользователя.')
                time.sleep(0.5)
                break
            elif command == 'contacts':
                with database_lock:
                    contacts_list = self.database.get_contacts()
                for contact in contacts_list:
                    print(contact)
            # Редактирование контактов
            elif command == 'edit':
                self.edit_contacts()

            elif command == 'history':
                self.print_history()
            else:
                print('Команда не распознана, попробойте снова, help - вывести поддерживаемые команды. ')

    def print_help(self):
        print('Поддерживаемые команды:')
        print('message - отправить сообщение. Кому и текст будет запрошены отдельно.')
        print('help - вывести подсказки по командам')
        print('exit - выход из программы')

    def print_history(self):
        """
        Функция выводящяя историю сообщений
        :return:
        """
        ask = input('Показать входящие сообщения - in, исходящие - out, все - просто Enter: ')
        with database_lock:
            if ask == 'in':
                history_list = self.database.get_history(to_who=self.account_name)
                for message in history_list:
                    print(f'\nСообщение от пользователя: {message[0]} '
                          f'от {message[3]}:\n{message[2]}')
            elif ask == 'out':
                history_list = self.database.get_history(from_who=self.account_name)
                for message in history_list:
                    print(f'\nСообщение пользователю: {message[1]} '
                          f'от {message[3]}:\n{message[2]}')
            else:
                history_list = self.database.get_history()
                for message in history_list:
                    print(f'\nСообщение от пользователя: {message[0]},'
                          f' пользователю {message[1]} '
                          f'от {message[3]}\n{message[2]}')

    def edit_contacts(self):
        ans = input('Для удаления введите del, для добавления add: ')
        if ans == 'del':
            edit = input('Введите имя удаляемного контакта: ')
            with database_lock:
                if self.database.check_contact(edit):
                    self.database.del_contact(edit)
                else:
                    client_logger.error('Попытка удаления несуществующего контакта.')
        elif ans == 'add':
            # Проверка на возможность такого контакта
            edit = input('Введите имя создаваемого контакта: ')
            if self.database.check_user(edit):
                with database_lock:
                    self.database.add_contact(edit)
                with sock_lock:
                    try:
                        add_contact(self.sock, self.account_name, edit)
                    except ServerError:
                        client_logger.error('Не удалось отправить информацию на сервер.')


# Класс-приёмник сообщений с сервера. Принимает сообщения, выводит в консоль.

class ClientReader(threading.Thread, metaclass=ClientMaker):
    def __init__(self, account_name, sock, database):
        self.account_name = account_name
        self.sock = sock
        self.database = database
        super().__init__()

    def run(self):
        while True:
            time.sleep(1)
            with sock_lock:
                try:
                    message = get_message(self.sock)

                    # Принято некорректное сообщение
                except IncorrectDataRecivedError:
                    client_logger.error(f'Не удалось декодировать полученное сообщение.')
                # Вышел таймаут соединения если errno = None, иначе обрыв соединения.
                except OSError as err:
                    if err.errno:
                        client_logger.critical(f'Потеряно соединение с сервером.')
                        break
                # Проблемы с соединением
                except (ConnectionError,
                        ConnectionAbortedError,
                        ConnectionResetError,
                        json.JSONDecodeError):
                    client_logger.critical(f'Потеряно соединение с сервером.')
                    break
                # Если пакет корретно получен выводим в консоль и записываем в базу.
                else:
                    if ACTION in message and message[ACTION] == MESSAGE \
                            and SENDER in message \
                            and DESTINATION in message \
                            and MESSAGE_TEXT in message \
                            and message[DESTINATION] == self.account_name:
                        print(f'\n Получено сообщение от пользователя '
                              f'{message[SENDER]}:\n{message[MESSAGE_TEXT]}')
                        # Захватываем работу с базой данных и сохраняем в неё сообщение
                        with database_lock:
                            try:
                                self.database.save_message(message[SENDER],
                                                           self.account_name,
                                                           message[MESSAGE_TEXT])
                            except Exception as e:
                                print(e)
                                client_logger.error('Ошибка взаимодействия с базой данных')


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
        exit(1)

    return server_address, server_port, client_name

# Функция запрос контакт листа
def contacts_list_request(sock, name):
    client_logger.debug(f'Запрос контакт листа для пользователя {name}')
    req = {
        ACTION: GET_CONTACTS,
        TIME: time.time(),
        USER: name
    }
    client_logger.debug(f'Сформирован запрос {req}')
    send_message(sock, req)
    ans = get_message(sock)
    client_logger.debug(f'Получен ответ {ans}')
    if RESPONSE in ans and ans[RESPONSE] == 202:
        return ans[LIST_INFO]
    else:
        raise ServerError

# Функция добавления пользователя в контакт лист
def add_contact(sock, username, contact):
    client_logger.debug(f'Создание контакта {contact}')
    req = {
        ACTION: ADD_CONTACT,
        TIME: time.time(),
        USER: username,
        ACCOUNT_NAME: contact
    }
    send_message(sock, req)
    ans = get_message(sock)
    if RESPONSE in ans and ans[RESPONSE] == 200:
        pass
    else:
        raise ServerError('Ошибка создания контакта')
    print('Удачное создание контакта.')

# Функция запроса списка известных пользователей
def user_list_request(sock, username):
    client_logger.debug(f'Запрос списка известных пользователей {username}')
    req = {
        ACTION: USERS_REQUEST,
        TIME: time.time(),
        ACCOUNT_NAME: username
    }
    send_message(sock, req)
    ans = get_message(sock)
    if RESPONSE in ans and ans[RESPONSE] == 202:
        return ans[LIST_INFO]
    else:
        raise ServerError

# Функция удаления пользователя из списка контактов
def remove_contact(sock, username, contact):
    client_logger.debug(f'Создание контакта {contact}')
    req = {
        ACTION: REMOVE_CONTACT,
        TIME: time.time(),
        USER: username,
        ACCOUNT_NAME: contact
    }
    send_message(sock, req)
    ans = get_message(sock)
    if RESPONSE in ans and ans[RESPONSE] == 200:
        pass
    else:
        raise ServerError('Ошибка удаления клиента')
    print('Удачное удаление')


# Функция инициализатор базы данных.
# Запускается при запуске, загружает данные в базу с сервера.
def database_load(sock, database, username):
    # Загружаем список известных пользователей
    try:
        users_list = user_list_request(sock, username)
    except ServerError:
        client_logger.error('Ошибка запроса списка известных пользователей.')
    else:
        database.add_users(users_list)

    # Загружаем список контактов
    try:
        contacts_list = contacts_list_request(sock, username)
    except ServerError:
        client_logger.error('Ошибка запроса списка контактов.')
    else:
        for contact in contacts_list:
            database.add_contact(contact)


def main():
    """Загружаем параметры командной строки"""
    server_address, server_port, client_name = arg_parser()

    """Сообщаем о запуске"""
    print(f'Консольный месседжер. Клиентский модуль. Имя пользователя: {client_name}')

    # Если имя пользователя не было задано, необходимо запросить пользователя
    if not client_name:
        client_name = input('Введите имя пользователя: ')
    else:
        print(f'Клиентский модуль запущен с именем: {client_name}')

    client_logger.info(
        f'Запущен клиент с парамертами: адрес сервера: {server_address}, '
        f'порт: {server_port}, режим работы: {client_name}'
    )

    # Инициализация сокета и сообщение серверу о нашем появлении
    try:
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.settimeout(1)
        transport.connect((server_address, server_port))
        send_message(transport, create_presence(client_name))
        answer = process_ans(get_message(transport))
        client_logger.info(f'Установлено соединение с сервером. Ответ сервера: {answer}')
        print(f'Установлено соединение с сервером.')
    except json.JSONDecodeError:
        client_logger.error('Не удалось декодировать полученную Json строку.')
        exit(1)
    except ServerError as error:
        client_logger.error(f'При установке соединения сервер вернул ошибку: {error.text}')
        exit(1)
    except ReqFieldMissingError as missing_error:
        client_logger.error(f'В ответе сервера отсутствует необходимое поле {missing_error.missing_field}')
        exit(1)
    except (ConnectionRefusedError, ConnectionError):
        client_logger.critical(
            f'Не удалось подключиться к серверу {server_address}:{server_port}, '
            f'конечный компьютер отверг запрос на подключение.'
        )
        exit(1)
    else:
        # Инициализация БД
        database = ClientDatabase(client_name)
        database_load(transport, database, client_name)

        """Если соединение с сервером установлено корректно,
        запускаем клиентский процесс приёма сообщений"""
        module_reciver = ClientReader(client_name, transport)
        module_reciver.daemon = True
        module_reciver.start()

        # затем запускаем отправку сообщений и взаимодействие с пользователем.
        module_sender = ClientSender(client_name, transport, database)
        module_sender.daemon = True
        module_sender.start()
        client_logger.debug('Запущены процессы')

        # Watchdog основной цикл, если один из потоков завершён, то значит или потеряно соединение, или пользователь
        # ввёл exit. Все события обработываются в потоках, достаточно просто завершить цикл.
        while True:
            time.sleep(1)
            if module_reciver.is_alive() and module_sender.is_alive():
                continue
            break


if __name__ == '__main__':
    main()
