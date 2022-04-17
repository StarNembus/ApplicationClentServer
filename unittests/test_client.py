import sys
import os
import unittest
import time


from client import create_presence, process_ans, fill_param_and_init_socket
from common.utils import get_message
from common.variables import ACTION, ACCOUNT_NAME, RESPONSE, PRESENCE, TIME, USER, \
    ERROR


sys.path.append(os.path.join(os.getcwd(), '..'))


class TestClient(unittest.TestCase):

    def test_create_presence(self):
        account_name = 'Guest'
        obj = {
            ACTION: PRESENCE,
            TIME: time.time(),
            USER: {
                ACCOUNT_NAME: account_name
            }
        }
        self.assertEqual(create_presence()[ACTION], obj[ACTION])
        self.assertEqual(create_presence()[USER], obj[USER])


class TestProcess(unittest.TestCase):
    """
    Тест проверяет ответ метода process_ans
    """

    ok_msg = '200: OK'

    def test_ok_check(self):
        transport = fill_param_and_init_socket()
        self.assertEqual(process_ans(get_message(transport)), self.ok_msg)


