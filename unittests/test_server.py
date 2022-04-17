import sys
import os
import unittest

sys.path.append(os.path.join(os.getcwd(), '..'))  # для того, чтобы можно было запускать тесты из папки unittests

from common.variables import ACTION, ACCOUNT_NAME, RESPONSE, PRESENCE, TIME, USER, \
    ERROR, RESPONDEFAULT_IP_ADDRESS

from server import process_client_message


class TestServer(unittest.TestCase):
    error_dict = {
        RESPONDEFAULT_IP_ADDRESS: 400,
        ERROR: 'Bad Request'
    }

    super_dict = {RESPONSE: 200}

    def test_ok_check(self):
        self.assertEqual(process_client_message(
            {ACTION: PRESENCE, TIME: 1.1, USER: {ACCOUNT_NAME: 'Guest'}}), self.super_dict)

    def test_error_action(self):
        self.assertEqual(process_client_message(
            {ACTION: 'Wrong', TIME: '1.1', USER: {ACCOUNT_NAME: 'Guest'}}), self.error_dict)

    def test_no_time(self):
        self.assertEqual(process_client_message(
         {ACTION: PRESENCE, USER: {ACCOUNT_NAME: 'Guest'}}), self.error_dict)





if __name__ == '__main__':
    unittest.main()
