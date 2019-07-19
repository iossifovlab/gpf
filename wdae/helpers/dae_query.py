from __future__ import unicode_literals
from builtins import str
import logging


LOGGER = logging.getLogger(__name__)


def columns_to_labels(columns, column_labels):
    return [column_labels[column] for column in columns]


def join_line(l, sep='\t'):
    tl = map(lambda v: '' if v is None or v == 'None' else str(v), l)
    return sep.join(tl) + '\n'
