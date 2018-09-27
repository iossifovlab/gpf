import random
import string
from os import getcwd
from box import Box

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


def get_opts(score_file=None, conf=None, search_cols=[]):
    options = {
        'c': 'chrom',
        'p': 'pos',
        'v': 'variant',
        'H': False,
        'search_columns': ','.join(search_cols),
        'scores_file': score_file,
        'scores_config_file': conf,
        'scores_directory': getcwd()+'/test_multiple_scores_tmpdir',
        'scores': 'score1,score2',
        'direct': False,
        'frequency': 'all.altFreq'
    }
    return Box(options, default_box=True, default_box_attr=None)
