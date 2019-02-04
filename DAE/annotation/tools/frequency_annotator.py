#!/usr/bin/env python
from __future__ import print_function

import os
import sys

from annotation.tools.annotator_base import VariantAnnotatorBase
from annotation.tools import score_file_io


class FrequencyAnnotator(VariantAnnotatorBase):

    def __init__(self, config):
        super(FrequencyAnnotator, self).__init__(config)

        assert self.config.options.freq
        assert self.config.columns_config['output']

        self.freq_cols = self.config.options.freq.replace(' ', '').split(',')
        self.output_cols = (self.config.columns_config['output']
                            .replace(' ', '').split(','))
        self.config.output_columns = self.output_cols
        assert len(self.freq_cols) == len(self.output_cols)

        self._init_freq_file()

        for freq_col in self.freq_cols:
            assert freq_col in self.freq_file.schema.col_names, \
                "{} not in {}".format(freq_col,
                                      self.freq_file.schema.col_names)

        assert self.variant_col_name in self.freq_file.schema.col_names, \
            "'{}' not in {}".format(self.variant_col_name,
                                    self.freq_file.schema.col_names)

    def _init_freq_file(self):
        if not self.config.options.freq_file:
            print("You should provide a freq file location.", file=sys.stderr)
            sys.exit(1)

        freq_filename = os.path.abspath(self.config.options.freq_file)
        if not os.path.exists(freq_filename):
            wd = os.environ.get("DAE_DB_DIR", ".")
            freq_filename = os.path.join(wd, self.config.options.freq_file)
            freq_filename = os.path.abspath(freq_filename)
        assert os.path.exists(freq_filename), freq_filename

        self.freq_filename = freq_filename.split('/')[-1]

        assert self.config.options.freq is not None

        if self.config.options.direct:
            self.freq_file = score_file_io.DirectAccess(
                self.config.options,
                freq_filename,
                config_filename=None,
                score_config=None)
        else:
            self.freq_file = score_file_io.IterativeAccess(
                self.config.options,
                freq_filename,
                config_filename=None,
                score_config=None)
        self.freq_file._setup()

        self.no_score_value = self.freq_file.no_score_value
        if self.no_score_value.lower() in set(['na', 'none']):
            self.no_score_value = None

        self.variant_col_name = self.freq_file.config.columns.variant
        assert self.variant_col_name

    def collect_annotator_schema(self, schema):
        super(FrequencyAnnotator, self).collect_annotator_schema(schema)
        for index, freq_col in enumerate(self.freq_cols):
            schema.columns[self.output_cols[index]] = \
                    self.freq_file.schema.columns[freq_col]

    def _freq_not_found(self, aline):
        for output_col in self.output_cols:
            aline[output_col] = self.no_score_value

    def do_annotate(self, aline, variant):
        if variant is None:
            self._freq_not_found(aline)
            return
        chrom = variant.chromosome
        pos = variant.details.cshl_position

        scores = self.freq_file.fetch_scores(chrom, pos, pos)
        if not scores:
            self._freq_not_found(aline)
            return
        variant = variant.details.cshl_variant

        found = False
        for index, score_variant in enumerate(scores[self.variant_col_name]):
            if score_variant == variant:
                found = True
                for output_index, freq_col in enumerate(self.freq_cols):
                    values = scores[freq_col]
                    aline[self.output_cols[output_index]] = \
                        float(values[index])  # FIXME:
        if not found:
            print('FREQ: {} frequency score not found for variant {}:{} {}'.
                  format(self.freq_filename,
                         str(chrom), str(pos), str(variant)),
                  file=sys.stderr)
