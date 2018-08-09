import sys
import gzip
import pysam
import re
import ConfigParser
from utilities import AnnotatorBase, assign_values
from os.path import exists
from box import Box


class MyConfigParser(ConfigParser.SafeConfigParser):
    """
    Modified ConfigParser.SafeConfigParser
    that allows ':' in keys and only '=' as separator.
    """
    OPTCRE = re.compile(
        r'(?P<option>[^=\s][^=]*)'          # allow only =
        r'\s*(?P<vi>[=])\s*'                # for option separator
        r'(?P<value>.*)$'
        )


class ScoreFile(object):

    def __init__(self, score_file_name, config_input):
        self.name = score_file_name
        self.load_config(config_input)

    def load_config(self, config_input=None):
        # try default config path
        if config_input is None:
            config_input = self.name + '.conf'
        # config is dict case
        if isinstance(config_input, dict):
            self.config = Box(config_input,
                              default_box=True, default_box_attr=None)
        elif exists(config_input):
            with open(config_input, 'r') as config_file:
                conf_parser = MyConfigParser()
                conf_parser.optionxform = str
                conf_parser.readfp(config_file)

                conf_settings = dict(conf_parser.items('general'))
                conf_settings_cols = dict(conf_parser.items('columns'))
                conf_settings.update(conf_settings_cols)
                self.config = Box(conf_settings, default_box=True, default_box_attr=None)
        else:
            sys.stderr.write("You must provide a configuration \
                              file for the score file.\n")
            sys.exit(-78)

        self.file = gzip.open(self.name, 'rb')
        if self.config.header is None:
            header_str = self.file.readline().rstrip('\n')
            if header_str[0] == '#':
                header_str = header_str[1:]
            self.config.header = header_str.split('\t')
        else:
            self.config.header = self.config.header.split(',')

        if self.config.columns.search is not None:
            self.config.columns.search = self.config.columns.search.split(',')
            self.search_indices = [self.config.header.index(col)
                                   for col in self.config.columns.search]
        else:
            self.search_indices = []

        self.config.columns.score = self.config.columns.score.split(',')
        self.scores_indices = [self.config.header.index(col)
                               for col in self.config.columns.score]

    def get_scores(self, chr, pos, *args):
        args = list(args)
        try:
            for line in self._fetch(chr, pos):
                if args == [line[i] for i in self.search_indices]:
                    return [line[i] for i in self.scores_indices]
        except ValueError:
            pass
        return [self.config.noScoreValue]


class IterativeAccess(ScoreFile):

    XY_INDEX = {'X': 23, 'Y': 24}

    def __init__(self, score_file_name, score_config=None):
        super(IterativeAccess, self).__init__(score_file_name, score_config)

        self.chr_index = \
            self.config.header.index(self.config.columns.chr)
        self.pos_begin_index = \
            self.config.header.index(self.config.columns.pos_begin)
        self.pos_end_index = \
            self.config.header.index(self.config.columns.pos_end)
        if self._next_line():
            self.current_lines = [self._next_line_buf]
        else:
            sys.stderr.write("The file provided is empty.\n")
            sys.exit(-78)

    def _fetch(self, chr, pos):
        # TODO this implements closed interval because we want to support
        # files with single position column
        chr = self._chr_to_int(chr)

        for i in range(len(self.current_lines) - 1, -1, -1):
            if self._chr_to_int(self.current_lines[i][self.chr_index]) < chr or \
                    int(self.current_lines[i][self.pos_end_index]) < pos:
                del self.current_lines[0:i+1]
                break

        if len(self.current_lines) == 0 or \
                (int(self.current_lines[-1][self.pos_begin_index]) <= pos and
                 self._chr_to_int(self.current_lines[-1][self.chr_index]) <= chr):

            if self._next_line():
                line = self._next_line_buf
                while self._chr_to_int(line[self.chr_index]) <= chr and \
                        (int(line[self.pos_end_index]) < pos or
                         self._chr_to_int(line[self.chr_index]) != chr):
                    line = self._next_line_buf
                    if not self._next_line():
                        break
                self.current_lines.append(line)

            while int(self.current_lines[-1][self.pos_begin_index]) <= pos and \
                    self._chr_to_int(self.current_lines[-1][self.chr_index]) <= chr:
                if self._next_line():
                    self.current_lines.append(self._next_line_buf)
                else:
                    break

        return self.current_lines

    def _next_line(self):
        self._next_line_buf = self.file.readline()
        if self._next_line_buf is None \
                or self._next_line_buf == '':
            return False
        else:
            self._next_line_buf = \
                    self._next_line_buf.rstrip('\n').split('\t')
            return True

    def _chr_to_int(self, chr):
        chr = chr.replace('chr', '')
        return self.XY_INDEX.get(chr) or int(chr)


class DirectAccess(ScoreFile):

    def __init__(self, score_file_name, score_config=None):
        super(DirectAccess, self).__init__(score_file_name, score_config)
        self.file = pysam.Tabixfile(score_file_name)

    def _fetch(self, chr, pos):
        return self.file.fetch(chr, pos-1, pos, parser=pysam.asTuple())


class ScoreAnnotator(AnnotatorBase):

    def __init__(self, opts, header=None, search_columns=[]):
        super(ScoreAnnotator, self).__init__(opts, header)
        self.labels = opts.labels.split(',') if opts.labels else None
        self._init_score_file()
        self.search_columns = search_columns
        self._init_cols()

    def _init_cols(self):
        opts = self.opts
        header = self.header
        if opts.x is None and opts.c is None:
            opts.x = "location"

        chr_col = assign_values(opts.c, header)
        pos_col = assign_values(opts.p, header)
        loc_col = assign_values(opts.x, header)

        self.arg_columns = [chr_col, pos_col, loc_col] + \
            [assign_values(col, header) for col in self.search_columns]

    def _init_score_file(self):
        if not self.opts.scores_file:
            sys.stderr.write("You should provide a score file location.\n")
            sys.exit(-78)
        else:
            if self.opts.direct:
                self.file = DirectAccess(self.opts.scores_file,
                                         self.opts.scores_config_file)
            else:
                self.file = IterativeAccess(self.opts.scores_file,
                                            self.opts.scores_config_file)
        self.header.append(self.labels if self.labels
                           else self.file.config.scores_columns)

    @property
    def new_columns(self):
        return self.file.config.columns.score

    def _get_scores(self, new_columns, chr=None, pos=None, loc=None, *args):
        if loc is not None:
            chr, pos = loc.split(':')
        if chr != '':
            return self.file.get_scores(chr, int(pos), *args)
        else:
            return ['' for col in new_columns]

    def line_annotations(self, line, new_columns):
        params = [line[i-1] if i is not None else None for i in self.arg_columns]
        return self._get_scores(new_columns, *params)
