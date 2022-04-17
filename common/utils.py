"""Утилиты"""

import json
from common.variables import MAX_PACKAGE_LENGTH, ENCODING
from errors import NonDictInputError, IncorrectDataRecivedError


def get_message(client):
    """
    Прием и декодирование сообщения
    принимает байты, выдает словарь
    выдает ошибку в случае если принимает что-либо другое
    :param client:
    :return:
    """
    encoded_response = client.recv(MAX_PACKAGE_LENGTH)
    if isinstance(encoded_response, bytes):
        json_response = encoded_response.decode(ENCODING)
        response = json.loads(json_response)
        if isinstance(response, dict):
            return response
        else:
            raise IncorrectDataRecivedError
    else:
        raise IncorrectDataRecivedError


def send_message(sock, message):
    """
    Кодирование и отправка сообщения
    принимает словарь и отправляет его
    :param sock:
    :param message:
    :return:
    """
    if not isinstance(message, dict):
        raise NonDictInputError
    js_message = json.dumps(message)
    encoded_message = js_message.encode(ENCODING)
    sock.send(encoded_message)