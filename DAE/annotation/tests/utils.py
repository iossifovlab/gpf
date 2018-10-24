
import random
import string
from box import Box
import os


def relative_to_this_test_folder(path):
    return os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        path
    )


class Dummy_tbi:

    def __init__(self, filename):
        print(filename, type(filename))
        if isinstance(filename, str):
            self.file = open(filename, 'r')
        else:
            self.file = filename

    def get_splitted_line(self):
        print(self.file, type(self.file))

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
        where = os.getcwd()
    if name is None:
        name = ''.join(
            random.choice(string.ascii_lowercase) for i in range(3)) + suffix
    name = where + '/' + name
    temp = open(name, 'w')
    temp.write(content)
    temp.seek(0)
    temp.close()
    return temp.name


def get_test_annotator_opts(score_file=None, conf=None, search_cols=[]):
    options = {
        'c': 'chrom',
        'p': 'pos',
        'v': 'variant',
        'H': False,
        'search_columns': ','.join(search_cols),
        'scores_file': score_file,
        'scores_config_file': conf,
        'scores_directory': os.getcwd()+'/test_multiple_scores_tmpdir',
        'scores': 'score1,score2',
        'direct': False,
        'frequency': 'all.altFreq'
    }
    return Box(options, default_box=True, default_box_attr=None)
