import random
import string
from os import getcwd

class Dummy_tbi:

    def __init__(self, filename):
        if type(filename) is str:
            self.file = open(filename, 'r')
        else:
            self.file = filename

    def get_splitted_line(self):
        res = self.file.readline().rstrip('\n')
        if res == '':
            return res
        else:
            return res.split('\t')

    def fetch(self, region, parser):
        return iter(self.get_splitted_line, '')


def dummy_gzip_open(filename, *args, **kwargs):
    if type(filename) is str:
        return open(filename, 'r')
    else:
        return filename


def to_file(content, name=None, where=None, suffix='.temp'):
    if where is None:
        where = getcwd()
    if name is None:
        name = ''.join(random.choice(string.ascii_lowercase) for i in range(3)) + suffix
    name = where + '/' + name
    temp = open(name, 'w')
    temp.write(content)
    temp.seek(0)
    temp.close()
    return temp.name
