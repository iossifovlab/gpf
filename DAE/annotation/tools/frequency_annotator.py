#!/usr/bin/env python
from __future__ import print_function
import sys
from os.path import basename
from annotation.tools.score_annotator import VariantScoreAnnotatorBase


class FrequencyAnnotator(VariantScoreAnnotatorBase):

    def __init__(self, config):
        super(FrequencyAnnotator, self).__init__(config)

    def _init_score_file(self):
        super(FrequencyAnnotator, self)._init_score_file()

        self.score_filename_base = basename(self.score_file.filename)
        self.variant_col_name = self.score_file.config.columns.variant
        assert self.variant_col_name
        assert self.variant_col_name in self.score_file.schema.col_names, \
            "'{}' not in score file schema!".format(
                    self.variant_col_name, self.score_file.schema.col_names)

    def collect_annotator_schema(self, schema):
        super(FrequencyAnnotator, self).collect_annotator_schema(schema)

    def do_annotate(self, aline, variant):
        if variant is None:
            self._scores_not_found(aline)
            return
        chrom = variant.chromosome
        pos = variant.details.cshl_position

        scores = self.score_file.fetch_scores(chrom, pos, pos)
        if not scores:
            self._scores_not_found(aline)
            return
        variant = variant.details.cshl_variant

        variant_occurrences = scores[self.variant_col_name].count(variant)
        if variant_occurrences > 0:
            if variant_occurrences > 1:
                print('WARNING {}: multiple variant occurrences of {}:{} {}'.
                      format(self.score_filename_base,
                             str(chrom), str(pos), str(variant)),
                      file=sys.stderr)

            variant_index = scores[self.variant_col_name].index(variant)
            for native, output in self.config.columns_config.items():
                # FIXME: this conversion should come from schema
                val = scores[native][variant_index]
                try:
                    if val in set(['', ' ']):
                        aline[output] = self.no_score_value
                    else:
                        aline[output] = float(val)
                except ValueError as ex:
                    print("problem with: ", output, chrom, pos, [val],
                          file=sys.stderr)
                    raise ex
        # else:
        #     print('{}: frequency score not found for variant {}:{} {}'.
        #           format(self.score_filename_base,
        #                  str(chrom), str(pos), str(variant)),
        #           file=sys.stderr)
