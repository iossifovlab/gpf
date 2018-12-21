import sys
import os
import pyBigWig

from annotation.tools.score_file_io import ScoreFile, LineAdapter
from annotation.tools.schema import Schema


class BigWigLineAdapter(LineAdapter):

    def __init__(self, line):
        self.line = list(line)

    @property
    def pos_begin(self):
        return self.line[1] + 1

    @property
    def pos_end(self):
        return self.line[2]

    @property
    def chrom(self):
        return self.line[0]


class BigWigFile(ScoreFile):

    def __init__(self, score_filename):
        assert os.path.exists(score_filename)
        self.bwfile = pyBigWig.open(score_filename)
        self.filename = score_filename

    def _init_chrom_prefix(self):
        chr_sample = list(self.bwfile.chroms().keys())[0]
        self._has_chrom_prefix = 'chr' in chr_sample

    def _handle_chrom_prefix(self, chrom):
        return super(BigWigFile, self)._handle_chrom_prefix(chrom)

    def _setup(self):
        score_name = os.path.basename(self.filename)
        score_name = score_name[:score_name.index('.')]
        self.header = ['chrom', 'pos_begin', 'pos_end', score_name]
        self.score_names = [score_name]
        self.no_score_value = 'na'
        self.schema = Schema.from_dict({
            'str': 'chrom',
            'int': 'pos_begin, pos_end',
            'float': score_name})
        self._init_chrom_prefix()

    def _load_config(self, config_filename=None):
        raise NotImplementedError()

    def _setup_config(self, score_config):
        raise NotImplementedError()

    def _fetch(self, chrom, pos_begin, pos_end):
        result = []
        try:
            score_values = self.bwfile.intervals(chrom, pos_begin - 1, pos_end)
            if score_values:
                for line in score_values:
                    result.append(BigWigLineAdapter([chrom, *line]))
        except RuntimeError:
            print('No scores found for interval {}:{}-{}!'
                  .format(chrom, pos_begin, pos_end),
                  file=sys.stderr)
        return result
