import json
import sys
import os
import unittest

sys.path.append(os.path.join(os.getcwd(), '..'))

from common.variables import ACTION, ACCOUNT_NAME, RESPONSE, PRESENCE, TIME, USER, \
    ERROR, ENCODING

from common.utils import get_message, send_message


class TestSocket:
    def __init__(self, test_dict):
        self.test_dict = test_dict
        self.encoded_message = None
        self.recevied_message = None

    def send(self, message_to_send):
        json_test_message = json.dumps(self.test_dict)
        self.encoded_message = json_test_message.encode(ENCODING)
        self.recevied_message = message_to_send

    def recv(self, max_len):
        json_test_message = json.dumps(self.test_dict)
        return json_test_message.encode(ENCODING)


class TestUtils(unittest.TestCase):
    test_dict_send = {
        ACTION: PRESENCE,
        TIME: 111111.111111,
        USER: {
            ACCOUNT_NAME: 'test_test'
        }
    }
    test_dict_recv_ok = {RESPONSE: 200}
    test_dict_recv_err = {
        RESPONSE: 400,
        ERROR: 'Bad Request'
    }

    def test_send_message(self):
        # экземпляр тестового словаря, хранит тестовый словарь
        test_socket = TestSocket(self.test_dict_send)

        # вызов тестируемой функции, результаты будут сохранены в тестовом сокете
        send_message(test_socket, self.test_dict_send)

        # проверка корректности кодирования словаря
        # сравниваем результат доверенного кодирования и результат от тестируемой функции
        self.assertEqual(test_socket.encoded_message, test_socket.recevied_message)


        # self.assertRaises(TypeError, send_message, test_socket, 'wrong_dictionary')


    def test_get_message(self):
        test_sock_ok = TestSocket(self.test_dict_recv_ok)
        test_sock_err = TestSocket(self.test_dict_recv_err)

        get_message(test_sock_ok)
        get_message(test_sock_err)

        self.assertEqual(test_sock_ok.encoded_message, test_sock_ok.recevied_message)
        self.assertEqual(test_sock_err.encoded_message, test_sock_err.recevied_message)












