import logging


LOGGER = logging.getLogger(__name__)


def join_line(l, sep='\t'):
    tl = map(lambda v: '' if v is None or v == 'None' else str(v), l)
    return sep.join(tl) + '\n'
