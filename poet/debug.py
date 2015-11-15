import logging
from datetime import datetime

DATE_FMT = '%m/%d/%y %H:%M:%S'

logging.basicConfig(format='%(message)s', level=logging.INFO)


def disable():
    logging.basicConfig(format='%(message)s', level=None)


def _debug_print(msg, symbol='+'):
    logging.info('[{}] ({}) {}'.format(symbol,
                 datetime.now().strftime(DATE_FMT), msg))


def info(msg):
    _debug_print(msg)


def warn(msg):
    _debug_print(msg, '!')


def err(msg):
    _debug_print(msg, '-')
