from __future__ import print_function

import sys
import os
import pyBigWig

from annotation.tools.score_file_io import ScoreFile, LineAdapter
from annotation.tools.schema import Schema


class BigWigLineAdapter(LineAdapter):

    def __init__(self, chromosome, line):
        self.chromosome = chromosome
        self.line = line

    @property
    def pos_begin(self):
        return self.line[0] + 1

    @property
    def pos_end(self):
        return self.line[1]

    @property
    def chrom(self):
        return self.chromosome

    def __getitem__(self, index):
        if index == 0:
            return self.chromosome
        else:
            return self.line[index - 1]


class BigWigFile(ScoreFile):

    def __init__(self, score_filename, config_filename=None):
        assert os.path.exists(score_filename)
        self.filename = score_filename
        self.bwfile = pyBigWig.open(score_filename)
        assert self.bwfile
        self._load_config(config_filename)

    def _setup(self):
        self.header = ['chrom', 'pos_begin', 'pos_end', self.score_names[0]]
        self.schema = Schema()
        self.schema.create_column('chrom', 'str')
        self.schema.create_column('pos_begin', 'int')
        self.schema.create_column('pos_end', 'int')
        self.schema.create_column(self.score_names[0], 'float')

    def _cleanup(self):
        self.bwfile.close()

    def _setup_config(self, score_config):
        self.config = score_config
        assert self.config.format.lower() == 'bigwig'
        self.score_names = [self.config.columns.score]
        self.no_score_value = self.config.noScoreValue
        self._has_chrom_prefix = self.config.chr_prefix

    def _fetch(self, chrom, pos_begin, pos_end):
        result = []
        try:
            score_values = self.bwfile.intervals(chrom, pos_begin - 1, pos_end)
            if score_values:
                for line in score_values:
                    result.append(BigWigLineAdapter(chrom, line))
        except RuntimeError:
            print('No scores found for interval {}:{}-{}!'
                  .format(chrom, pos_begin, pos_end),
                  file=sys.stderr)
        return result
