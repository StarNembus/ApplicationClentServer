
import logging
import sys
import traceback


if sys.argv[0].find('client.py') == -1:
    logger = logging.getLogger('server')
else:
    logger = logging.getLogger('client')


def log(func_log):
    def decorate_log_server(*args, **kwargs):
        result = func_log(*args, **kwargs)
        logger.debug(f'Функция {func_log.__name__} с параметрами {args}, {kwargs}'
                     f'Вызов из функции {traceback.format_stack()[0].strip().split()[-1]}')
        return result

    return decorate_log_server
