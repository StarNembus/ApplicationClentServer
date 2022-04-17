"""Утилиты"""

import json
from common.variables import MAX_PACKAGE_LENGTH, ENCODING




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
        raise ValueError
    raise ValueError


def send_message(sock, message):
    """
    Кодирование и отправка сообщения
    принимает словарь и отправляет его
    :param sock:
    :param message:
    :return:
    """
    # if not isinstance(message, dict):
    #     raise TypeError
    js_message = json.dumps(message)  # с помощью dumps получаем строку
    encoded_message = js_message.encode(ENCODING)  # кодируем
    sock.send(encoded_message)  # получаем байты