import sys
import log.server_log_config
import log.client_log_config
import logging

if sys.argv[0].find('client') == -1:
    logger = logging.getLogger('server')
else:
    logger = logging.getLogger('client')


def log(func_to_log):
    def log_saver(*args, **kwargs):
        logger.debug(f'Была вызвана функция {func_to_log} с параметрами {args}, {kwargs}.'
                     f' Вызов из модуля {func_to_log}')
        ret = func_to_log(*args, **kwargs)
        return ret
    return log_saver

