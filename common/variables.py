# Порт по дефолту для сетевого взаимодействия
import logging

DEFAULT_PORT = 7777

# TCP по дефолту для подключения к клиенту
DEFAULT_IP_ADRESS = '127.0.0.1'

# Max очередь подключений
MAX_CONNECTIONS = 5

# Max длина сообщений в байтах
MAX_PACKAGE_LENGTH = 1024

ENCODING = 'utf-8'

# JIM ключи
ACTION = 'action'
TIME = 'time'
USER = 'user'
ACCOUNT_NAME = 'account_name'
SENDER = 'sender'
DESTINATION = 'to'

# Прочие ключи
PRESENCE = 'presence'
RESPONSE = 'response'
ERROR = 'error'
RESPONDEFAULT_IP_ADDRESS = 'respondefault_ip_address'
MESSAGE = 'message'
MESSAGE_TEXT = 'mess_text'
EXIT = 'exit'
GET_CONTACTS = 'get_contacts'
LIST_INFO = 'data_list'
REMOVE_CONTACT = 'remove'
ADD_CONTACT = 'add'
USERS_REQUEST = 'get_users'

LOGGING_LEVEL = logging.DEBUG

RESPONSE_200 = {RESPONSE: 200}
RESPONSE_400 = {
    RESPONSE: 400,
    ERROR: None
}

# База данных для хранения данных сервера:
SERVER_DATABASE = 'sqlite:///server_base.db3'
